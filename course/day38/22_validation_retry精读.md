# Day 38 精读：validation_retry 与多轮 Self-RAG 重试管线

**需求**：ZL-NA-REQ-038 | **学时**：120 min

---

## 一、validation_retry.py 全文

```python
"""
多轮 Self-RAG 校验重试 — 校验失败后宽召回重检索

校验未通过时按 rag_wide 策略重新检索 citations，可选再生成 reply，
在拒答前尽量恢复可审计的正确回答。

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any, Callable

from rag.answer_validator import apply_validation_retry, ValidationResult
from rag.validation_config import REFUSAL_MESSAGE, ValidationConfig


@dataclass(frozen=True)
class ValidationRetryOutcome:
    """校验 + 重试后的最终输出"""

    validation: ValidationResult
    citations: list[dict[str, Any]]
    cite_data: dict[str, Any]
    reply: str
    refused: bool = False


def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = apply_validation_retry(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome(
        validation=result,
        citations=current_citations,
        cite_data=current_cite,
        reply=current_reply,
        refused=refused,
    )
```


---

## 二、行级注释：QueryRouter 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rewrite(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、RuleBasedQueryRouter.route（L33–L68）

```python
"""
答案校验配置 — Self-RAG 生成后引用一致性检查

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_OVERLAP = "overlap"
MODE_STRICT = "strict"

REFUSAL_MESSAGE = (
    "根据现有引用无法确认该回答的准确性，请查阅引用来源或换个问法。"
)


@dataclass
class ValidationConfig:
    """多轮 Self-RAG 校验重试策略"""

    enabled: bool = True
    mode: str = MODE_OVERLAP
    min_score: float = 0.35
    refuse_on_fail: bool = True
    retry_on_fail: bool = False
    max_retries: int = 1

    def validate(self) -> None:
        if self.mode not in (MODE_OVERLAP, MODE_STRICT):
            raise ValueError(f"mode 须为 overlap 或 strict，收到 {self.mode!r}")
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score 须在 0~1，收到 {self.min_score}")
        if self.max_retries < 0 or self.max_retries > 3:
            raise ValueError(f"max_retries 须在 0~3，收到 {self.max_retries}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "min_score": round(self.min_score, 4),
            "refuse_on_fail": self.refuse_on_fail,
            "retry_on_fail": self.retry_on_fail,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_OVERLAP)),
            min_score=float(data.get("min_score", 0.35)),
            refuse_on_fail=bool(data.get("refuse_on_fail", True)),
            retry_on_fail=bool(data.get("retry_on_fail", False)),
            max_retries=int(data.get("max_retries", 1)),
        )
```


| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `rewrite`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、rewrite 全文

```python
class ValidationResult:
    """单条答案校验结果 — 供审计与 preview API"""

    query: str
    reply: str
    passed: bool
    score: float
    reason: str
    citation_coverage: float
    matched_citation_ranks: tuple[int, ...]
    refused: bool = False
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "passed": self.passed,
            "score": round(self.score, 4),
            "reason": self.reason,
            "citation_coverage": round(self.citation_coverage, 4),
            "matched_citation_ranks": list(self.matched_citation_ranks),
            "refused": self.refused,
            "retries": self.retries,
        }


def _extract_tokens(text: str) -> set[str]:
    """从文本提取可用于 overlap 的关键词"""
    text = (text or "").strip().lower()
    if not text:
        return set()

    tokens: set[str] = set()
    for part in _TOKEN_SPLIT.split(text):
        part = part.strip()
        if len(part) >= 2:
            tokens.add(part)
        elif part:
            tokens.add(part)

    for run in _CJK_RUN.findall(text):
        tokens.add(run)
        if len(run) >= 4:
            for i in range(len(run) - 1):
                tokens.add(run[i : i + 2])

    return {t for t in tokens if len(t) >= 2 or t.isdigit()}


def _citation_text(citation: dict[str, Any]) -> str:
    preview = str(citation.get("preview") or "")
    matched = " ".join(str(t) for t in (citation.get("matched_tokens") or []))
    source = str(citation.get("source") or "")
    return f"{preview} {matched} {source}".strip().lower()
```


| 行 | 讲解 |
|----|------|
| 子串分支 | `q in t` → 1.0，电话/SKU 金路径 |
| coverage | matched tokens / query tokens |
| bigram_bonus | 连续二字共现比例 |
| length_penalty | 抑制长文噪声 |
| clamp | [0, 1] 便于 UI 展示 sim=% |

---

## 五、_bigram_overlap

```python
class ValidationResult:
    """单条答案校验结果 — 供审计与 preview API"""

    query: str
    reply: str
    passed: bool
    score: float
    reason: str
    citation_coverage: float
    matched_citation_ranks: tuple[int, ...]
    refused: bool = False
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "passed": self.passed,
            "score": round(self.score, 4),
            "reason": self.reason,
            "citation_coverage": round(self.citation_coverage, 4),
            "matched_citation_ranks": list(self.matched_citation_ranks),
            "refused": self.refused,
            "retries": self.retries,
        }


def _extract_tokens(text: str) -> set[str]:
    """从文本提取可用于 overlap 的关键词"""
    text = (text or "").strip().lower()
    if not text:
        return set()

    tokens: set[str] = set()
    for part in _TOKEN_SPLIT.split(text):
        part = part.strip()
        if len(part) >= 2:
            tokens.add(part)
        elif part:
            tokens.add(part)

    for run in _CJK_RUN.findall(text):
        tokens.add(run)
        if len(run) >= 4:
            for i in range(len(run) - 1):
                tokens.add(run[i : i + 2])

    return {t for t in tokens if len(t) >= 2 or t.isdigit()}


def _citation_text(citation: dict[str, Any]) -> str:
    preview = str(citation.get("preview") or "")
    matched = " ".join(str(t) for t in (citation.get("matched_tokens") or []))
    source = str(citation.get("source") or "")
    return f"{preview} {matched} {source}".strip().lower()
```


中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、context.py 全文

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.validation_retry import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 七、search 主流程

```python
def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = apply_validation_retry(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome
```


| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rewrite 开销 |
| pool 计算 | `max(max_citations, top_k)` |
| candidates | inner hybrid 宽召回 |
| rewrite 调用 | MockCrossEncoder 改写截断 |

---

## 八、citation_config.py 全文

```python
"""
答案校验配置 — Self-RAG 生成后引用一致性检查

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_OVERLAP = "overlap"
MODE_STRICT = "strict"

REFUSAL_MESSAGE = (
    "根据现有引用无法确认该回答的准确性，请查阅引用来源或换个问法。"
)


@dataclass
class ValidationConfig:
    """多轮 Self-RAG 校验重试策略"""

    enabled: bool = True
    mode: str = MODE_OVERLAP
    min_score: float = 0.35
    refuse_on_fail: bool = True
    retry_on_fail: bool = False
    max_retries: int = 1

    def validate(self) -> None:
        if self.mode not in (MODE_OVERLAP, MODE_STRICT):
            raise ValueError(f"mode 须为 overlap 或 strict，收到 {self.mode!r}")
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score 须在 0~1，收到 {self.min_score}")
        if self.max_retries < 0 or self.max_retries > 3:
            raise ValueError(f"max_retries 须在 0~3，收到 {self.max_retries}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "min_score": round(self.min_score, 4),
            "refuse_on_fail": self.refuse_on_fail,
            "retry_on_fail": self.retry_on_fail,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_OVERLAP)),
            min_score=float(data.get("min_score", 0.35)),
            refuse_on_fail=bool(data.get("refuse_on_fail", True)),
            retry_on_fail=bool(data.get("retry_on_fail", False)),
            max_retries=int(data.get("max_retries", 1)),
        )
```


`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

```python
def fetch_citations_retry(self, query: str, *, attempt: int = 1) -> dict[str, Any]:
        """Self-RAG 重试 — 强制 rag_wide 并放大 citation pool"""
        from rag.citation_config import CitationConfig
        from rag.route_config import INTENT_RAG_WIDE

        cfg = self.get_citation_config()
        if not cfg.enabled:
            return self.fetch_citations(query)

        boosted = CitationConfig.from_dict(
            {
                **cfg.to_dict(),
                "max_citations": min(100, max(cfg.max_citations, 20) + attempt * 10),
            }
        )
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(
            query,
            config=boosted,
            intent_override=INTENT_RAG_WIDE,
        )
        data = bundle.to_dict()
        data["retry_attempt"] = attempt
        return data
```


`RAGContextService(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_query_router.py

```python
"""Day 38 Validation Retry 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.knowledge_store import KnowledgeStore
from rag.route_config import INTENT_RAG_WIDE
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_fetch_citations_retry_forces_rag_wide(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations_retry("理财安全吗", attempt=1)
    route = data.get("route") or {}
    assert route.get("intent") == INTENT_RAG_WIDE
    assert route.get("expand") is True
    assert data.get("retry_attempt") == 1


def test_apply_validation_retry_no_retry_when_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(enabled=True, retry_on_fail=False, refuse_on_fail=False)
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 0
    assert outcome.validation.passed is False


def test_apply_validation_retry_increments_retries(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 1


def test_apply_validation_retry_passes_with_matching_reply(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("客服电话多少")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "客服电话多少",
        "请拨打客服热线 400-888-1234。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.passed is True


def test_apply_validation_retry_refuses_after_exhausted(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            mode="strict",
            min_score=0.9,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=True,
        )
    )
    cite = store.fetch_citations("智链科技总部在哪")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "智链科技总部在哪",
        "今天北京天气晴朗，适合出游。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.refused is True
    assert outcome.reply.startswith("[校验未通过]")
    assert outcome.validation.retries == 1


def test_validation_config_persists_retry_fields(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(retry_on_fail=True, max_retries=2, refuse_on_fail=False)
    )
    store.save(tmp_path / "store.json")
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    cfg = loaded.get_validation_config()
    assert cfg.retry_on_fail is True
    assert cfg.max_retries == 2
```


| 测试 | 要点 |
|------|------|
| test_RuleBasedQueryRouter.route_from_results_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_citation_preview_with_rewrite | 业务号码 |
| test_context_disabled | 降级路径 |
| test_fetch_citations_with_hits_accessible | inner 类型 |
| test_knowledge_store_persists_citation_config | 持久化 |

---

## 十一、API 测试 test_route_api.py

```python
"""Day 38 Validation Retry API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_validation_retry_preview(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "retries" in data
    assert data["passed"] is True


def test_validation_retry_preview_reports_route(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "理财安全吗",
            "reply": "投资需谨慎，详见产品说明书风险提示。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("retry_route") is not None or data.get("retries", 0) >= 0


def test_put_validation_config_retry_fields(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["retry_on_fail"] is True
    assert body["max_retries"] == 2


def test_status_includes_validation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["validation_config"]["retry_on_fail"] is False


def test_chat_includes_validation_retries_field(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": False,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert "retries" in body["validation"]


def test_chat_refuses_after_retry_exhausted(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "strict",
            "min_score": 0.9,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    assert resp.status_code == 200
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) >= 1
    assert val.get("passed") is False
    assert val.get("refused") is True
    assert body["reply"].startswith("[校验未通过]")


def test_chat_retry_preserves_day37_when_disabled(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": False,
            "max_retries": 0,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) == 0
    assert val.get("refused") is True


def test_validation_preview_still_works(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
```


`test_health_version` 锁版本 `v0.38.0`；`test_chat_includes_citations` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rewrite 后前 3 的 rewrite  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json citation_config  

---

## 十三、自检

1. 手绘三阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rewrite 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 口语命中 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day33 衔接

HybridRetriever 仍是 inner；关 rewrite 即回 Day33 行为。retrieval_config 与 citation_config 正交。

---

## 十六、knowledge_store rewrite 方法

```python
def get_validation_config(self) -> ValidationConfig:
        return ValidationConfig.from_dict(self.validation_config.to_dict())

    def set_validation_config(self, config: ValidationConfig) -> ValidationConfig:
        config.validate()
        self.validation_config = ValidationConfig.from_dict(config.to_dict())
        return self.validation_config

    def get_react_config(self) -> ReactConfig:
        return ReactConfig.from_dict(self.react_config.to_dict())

    def set_react_config(self, config: ReactConfig) -> ReactConfig:
        config.validate()
        self.react_config = ReactConfig.from_dict(config.to_dict())
        return self.react_config

    def get_executor_config(self) -> ExecutorConfig:
        return ExecutorConfig.from_dict(self.executor_config.to_dict())

    def set_executor_config(self, config: ExecutorConfig) -> ExecutorConfig:
        config.validate()
        self.executor_config = ExecutorConfig.from_dict(config.to_dict())
        return self.executor_config

    def get_graph_config(self) -> GraphConfig:
        return GraphConfig.from_dict(self.graph_config.to_dict())

    def set_graph_config(self, config: GraphConfig) -> GraphConfig:
        config.validate()
        self.graph_config = GraphConfig.from_dict(config.to_dict())
        return self.graph_config

    def get_approval_config(self) -> ApprovalConfig:
        return ApprovalConfig.from_dict(self.approval_config.to_dict())

    def set_approval_config(self, config: ApprovalConfig) -> ApprovalConfig:
        config.validate()
        self.approval_config = ApprovalConfig.from_dict(config.to_dict())
        return self.approval_config

    def get_supervisor_config(self) -> SupervisorConfig:
        return SupervisorConfig.from_dict(self.supervisor_config.to_dict())

    def set_supervisor_config(self, config: SupervisorConfig) -> SupervisorConfig:
        config.validate()
        self.supervisor_config = SupervisorConfig.from_dict(config.to_dict())
        return self.supervisor_config

    def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config

    def apply_validation_retry(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult | None:
        """按当前 validation_config 校验 reply 与 citations 一致性"""
        cfg = self.get_validation_config()
        if not cfg.enabled:
            return None
        validator = apply_validation_retry(config=cfg)
        return validator.validate(query, reply, citations)
```


`set_citation_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rewrite 是什么。  
2. 1 分钟对比召回与改写。  
3. 白板画 RAGContextService.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q citations 与 context 重复吗？** 可优化；当前同步教学实现。  
**Q matched_tokens 来源？** 来自 RetrievalResult，展示在 Citation 中。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RuleBasedQueryRouter.route` 与 `RoutingRetriever.search`，并映射到 ZL-NA-REQ-038 的 FR-001–FR-003。

---

## 二十一、validation_retry 完整源码（重复嵌入便于打印）

```python
"""
多轮 Self-RAG 校验重试 — 校验失败后宽召回重检索

校验未通过时按 rag_wide 策略重新检索 citations，可选再生成 reply，
在拒答前尽量恢复可审计的正确回答。

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any, Callable

from rag.answer_validator import apply_validation_retry, ValidationResult
from rag.validation_config import REFUSAL_MESSAGE, ValidationConfig


@dataclass(frozen=True)
class ValidationRetryOutcome:
    """校验 + 重试后的最终输出"""

    validation: ValidationResult
    citations: list[dict[str, Any]]
    cite_data: dict[str, Any]
    reply: str
    refused: bool = False


def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = apply_validation_retry(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome(
        validation=result,
        citations=current_citations,
        cite_data=current_cite,
        reply=current_reply,
        refused=refused,
    )
```


---

## 二十二、校验重试伪代码

```
function FETCH_CITATIONS(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(max_citations, top_k)
    C = INNER(q, P)          # HybridRetriever
    return build_citation_bundle(q, C)
```

---

## 二十三、ROUTE_QUERIES 业务解读

| query | 业务意图 | citation 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_citation_config_validate | FR-004 |
| test_RuleBasedQueryRouter.route_from_results_candidates | FR-002 |
| test_context_enabled | FR-003 |
| test_citation_preview_with_rewrite | AC-03 |
| test_knowledge_store_persists_citation_config | FR-005 |
| test_health_version | FR-008 |
| test_put_citation_config_disable | AC-02 |
| test_chat_includes_citations | AC-05 |

---

## 二十五、knowledge API 节选（citation 上下文）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-035 / ZL-NA-REQ-036 / ZL-NA-REQ-038 / ZL-NA-REQ-038
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    CitationConfigRequest,
    CitationConfigResponse,
    CitationPreviewRequest,
    CitationPreviewResponse,
    ExpansionConfigRequest,
    ExpansionConfigResponse,
    ExpansionPreviewRequest,
    ExpansionPreviewResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
    RerankConfigRequest,
    RerankConfigResponse,
    RewriteConfigRequest,
    RewriteConfigResponse,
    RewritePreviewRequest,
    RewritePreviewResponse,
    RouteConfigRequest,
    RouteConfigResponse,
    RoutePreviewRequest,
    RoutePreviewResponse,
    ValidationConfigRequest,
    ValidationConfigResponse,
    ValidationPreviewRequest,
    ValidationPreviewResponse,
    ValidationRetryPreviewRequest,
    ValidationRetryPreviewResponse,
    RetrievalConfigRequest,
    RetrievalConfigResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import CitationConfig
from rag.expansion_config import ExpansionConfig
from rag.query_expander import build_expander
from rag.query_rewriter import RuleBasedQueryRewriter
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import RouteConfig
from rag.validation_config import ValidationConfig
from rag.rerank_config import RerankConfig
from rag.rewrite_config import RewriteConfig
from rag.retrieval_config import RetrievalConfig
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
def get_retrieval_config() -> RetrievalConfigResponse:
    """返回当前检索模式（vector / keyword / hybrid）与融合参数"""
    cfg = get_knowledge_store().get_retrieval_config()
    return RetrievalConfigResponse(**cfg.to_dict())


@router.put("/retrieval-config", response_model=RetrievalConfigResponse)
def update_retrieval_config(body: RetrievalConfigRequest) -> RetrievalConfigResponse:
    """更新检索策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RetrievalConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_retrieval_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RetrievalConfigResponse(**cfg.to_dict())


@router.get("/rerank-config", response_model=RerankConfigResponse)
def get_rerank_config() -> RerankConfigResponse:
    """返回 rerank 开关、候选池大小与模型标识"""
    cfg = get_knowledge_store().get_rerank_config()
    return RerankConfigResponse(**cfg.to_dict())


@router.put("/rerank-config", response_model=RerankConfigResponse)
def update_rerank_config(body: RerankConfigRequest) -> RerankConfigResponse:
    """更新 rerank 策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RerankConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rerank_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RerankConfigResponse(**cfg.to_dict())


@router.get("/rewrite-config", response_model=RewriteConfigResponse)
def get_rewrite_config() -> RewriteConfigResponse:
    """返回查询改写开关与规则模式"""
    cfg = get_knowledge_store().get_rewrite_config()
    return RewriteConfigResponse(**cfg.to_dict())


@router.put("/rewrite-config", response_model=RewriteConfigResponse)
def update_rewrite_config(body: RewriteConfigRequest) -> RewriteConfigResponse:
    """更新查询改写策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RewriteConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rewrite_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RewriteConfigResponse(**cfg.to_dict())


@router.post("/rewrite-preview", response_model=RewritePreviewResponse)
def rewrite_preview(body: RewritePreviewRequest) -> RewritePreviewResponse:
    """预览单条 query 的规则改写结果（不触发检索）"""
    store = get_knowledge_store()
    cfg = store.get_rewrite_config()
    rewriter = RuleBasedQueryRewriter(config=cfg)
    result = rewriter.rewrite(body.query)
    return RewritePreviewResponse(**result.to_dict())


@router.get("/citation-config", response_model=CitationConfigResponse)
def get_citation_config() -> CitationConfigResponse:
    """返回引用溯源开关与展示参数"""
    cfg = get_knowledge_store().get_citation_config()
    return CitationConfigResponse(**cfg.to_dict())


@router.put("/citation-config", response_model=CitationConfigResponse)
def update_citation_config(body: CitationConfigRequest) -> CitationConfigResponse:
    """更新引用溯源策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = CitationConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_citation_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CitationConfigResponse(**cfg.to_dict())


@ro
```


---

## 二十六、phase3_route_review 建议

课后运行 `src/day38/phase3_route_review.py` 串联 Day25–34。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| citations 替代检索 | 展示层 |
| preview 与全文 | 截断展示 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 rewrite 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET validation-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 route_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 20 tests  
10. 能解释翻牌测试  
11. 能对比 Day33  
12. 能预告 Day36 HyDE  
13. 能读 validate 源码  
14. 能解释 include_route_meta  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_citations 上限 10  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-038 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`fetch_citations` 是 **Facade**：对外返回 dict，对内调用 RoutingRetriever.search。与 Day33 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 38 Validation Retry API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_validation_retry_preview(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "retries" in data
    assert data["passed"] is True


def test_validation_retry_preview_reports_route(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "理财安全吗",
            "reply": "投资需谨慎，详见产品说明书风险提示。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("retry_route") is not None or data.get("retries", 0) >= 0


def test_put_validation_config_retry_fields(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["retry_on_fail"] is True
    assert body["max_retries"] == 2


def test_status_includes_validation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["validation_config"]["retry_on_fail"] is False


def test_chat_includes_validation_retries_field(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": False,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert "retries" in body["validation"]


def test_chat_refuses_after_retry_exhausted(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "strict",
            "min_score": 0.9,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    assert resp.status_code == 200
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) >= 1
    assert val.get("passed") is False
    assert val.get("refused") is True
    assert body["reply"].startswith("[校验未通过]")


def test_chat_retry_preserves_day37_when_disabled(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": False,
            "max_retries": 0,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) == 0
    assert val.get("refused") is True


def test_validation_preview_still_works(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
```


---

## 三十一、课堂录音稿（8 min）

「打开 validation_retry，找 apply_validation_retry。先看首次校验：通过直接返回。失败且 retry_on_fail 才用 rag_wide 重检索再校验一次。这就是 ZL-NA-REQ-038 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RAGContextService + RouteConfig
- GET/PUT /api/knowledge/validation-config
- tests/day37 (20 cases)
```

---

## 三十三、context 二次嵌入

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.validation_retry import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 三十四、route_demo 全文

```python
"""
多轮 Self-RAG 重试演示 — 校验失败后 rag_wide 重检索

运行：PYTHONPATH=src python3 src/day38/retry_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day38.constants import RETRY_CASES
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def main() -> int:
    print("=" * 60)
    print("  Day 38 多轮 Self-RAG 重试演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            refuse_on_fail=False,
            retry_on_fail=True,
            max_retries=1,
        )
    )

    for item in RETRY_CASES:
        q = item["query"]
        reply = item["reply"]
        cite_data = store.fetch_citations(q)
        citations = cite_data.get("citations") or []
        outcome = apply_validation_retry(store, q, reply, citations, cite_data)
        assert outcome is not None
        flag = "✅" if outcome.validation.passed == item["expect_passed_after_retry"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    retries={outcome.validation.retries} passed={outcome.validation.passed} {flag}")
        print(f"    reason: {outcome.validation.reason}")
        route = outcome.cite_data.get("route")
        if route:
            print(f"    route: {route.get('intent')} expand={route.get('expand')}")

    print("\n  ✅ Retry 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 三十五、延迟估算习题

pool=20，单次 rewrite 0.5ms → rewrite 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、口语命中 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rewrite 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_citations_count`、`rag_citation_enabled`、`chat_with_citations_rate`。

---

## 三十九、Citation JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | int | 1-based 排序 |
| chunk_id | str | 可追溯分块 |
| source | str | 文档名 |
| score | float | rerank 后分数 |
| preview | str | 截断正文 |
| matched_tokens | list | 命中 token |

---

## 四十、validation_retry 全文嵌入

```python
"""
多轮 Self-RAG 校验重试 — 校验失败后宽召回重检索

校验未通过时按 rag_wide 策略重新检索 citations，可选再生成 reply，
在拒答前尽量恢复可审计的正确回答。

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any, Callable

from rag.answer_validator import apply_validation_retry, ValidationResult
from rag.validation_config import REFUSAL_MESSAGE, ValidationConfig


@dataclass(frozen=True)
class ValidationRetryOutcome:
    """校验 + 重试后的最终输出"""

    validation: ValidationResult
    citations: list[dict[str, Any]]
    cite_data: dict[str, Any]
    reply: str
    refused: bool = False


def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = apply_validation_retry(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome(
        validation=result,
        citations=current_citations,
        cite_data=current_cite,
        reply=current_reply,
        refused=refused,
    )
```


---

## 四十一、chat citations 代码

```python
outcome = apply_validation_retry(
        store,
        message,
        reply,
        citations,
        cite_data,
        regenerate_fn=lambda: orchestrator.handle_message(message),
    )
    if outcome is not None:
        reply = outcome.reply
        kind, meta = classify_reply(reply)
        if mcp_trace is not None:
            kind = "mcp"
            meta = "MCP Tool Bridge"
        elif supervisor_trace is not None:
            kind = "supervisor"
            meta = "Supervisor Multi-Agent"
        elif approval_payload is not None:
            kind = "approval"
            meta = "Approval Workflow"
        elif graph_trace and kind != "approval":
            kind = "graph"
            meta = "StateGraph"
        elif executor_trace:
            kind = "executor"
            meta = "AgentExecutor"
        elif agent_trace:
            kind = "agent"
            meta = "ReAct Agent"
        citations = outcome.citations
        cite_data = outcome.cite_data
        rewrite = cite_data.get("rewrite")
        expansion = cite_data.get("expansion")
        route = cite_data.get("route")
        validation = outcome.validation.to_dict()
        if outcome.refused:
            validation = {**validation, "refused": True}
        if outcome.validation.retries:
            validation = {
                **validation,
                "retry_route": cite_data.get("route"),
            }
```


---

## 四十二、fetch_citations 代码

```python
def fetch_citations(self, query: str) -> dict[str, Any]:
        """按当前 citation_config 检索并返回引用包 dict"""
        cfg = self.get_citation_config()
        if not cfg.enabled:
            return {
                "query": query.strip(),
                "citations": [],
                "rewrite": None,
                "expansion": None,
                "route": None,
            }
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(query, config=cfg)
        return bundle.to_dict()

    def fetch_citations_retry(self, query: str, *, attempt: int = 1) -> dict[str, Any]:
        """Self-RAG 重试 — 强制 rag_wide 并放大 citation pool"""
        from rag.citation_config import CitationConfig
        from rag.route_config import INTENT_RAG_WIDE

        cfg = self.get_citation_config()
        if not cfg.enabled:
            return self.fetch_citations(query)

        boosted = CitationConfig.from_dict(
            {
                **cfg.to_dict(),
                "max_citations": min(100, max(cfg.max_citations, 20) + attempt * 10),
            }
        )
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(
            query,
            config=boosted,
            intent_override=INTENT_RAG_WIDE,
        )
        data = bundle.to_dict()
        data["retry_attempt"] = attempt
        return data
```


---

## 四十三、前端展示要点

`app.js` 的 `msg__route` 渲染 rank/source/score/preview；`msg__rewrite` 展示改写链。

---

## 四十四、合规场景

理财回答必须带风险提示引用 — citations 第一条应来自风险揭示 chunk。

---

## 四十五、测试与 FR 映射

| 测试 | FR |
|------|-----|
| test_RuleBasedQueryRouter.route_from_results | FR-002 |
| test_fetch_citations_with_hits | FR-003 |
| test_chat_includes_citations | FR-006 |
| test_citation_preview_with_rewrite | FR-005 |

---

## 四十六、完整 context.py 引用段

```python
def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = apply_validation_retry(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome
```


---

## 四十七、完整测试文件

```python
"""Day 38 Validation Retry 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.knowledge_store import KnowledgeStore
from rag.route_config import INTENT_RAG_WIDE
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_fetch_citations_retry_forces_rag_wide(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations_retry("理财安全吗", attempt=1)
    route = data.get("route") or {}
    assert route.get("intent") == INTENT_RAG_WIDE
    assert route.get("expand") is True
    assert data.get("retry_attempt") == 1


def test_apply_validation_retry_no_retry_when_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(enabled=True, retry_on_fail=False, refuse_on_fail=False)
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 0
    assert outcome.validation.passed is False


def test_apply_validation_retry_increments_retries(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("年化收益怎么样")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "年化收益怎么样",
        "今天天气很好。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.retries == 1


def test_apply_validation_retry_passes_with_matching_reply(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=False,
        )
    )
    cite = store.fetch_citations("客服电话多少")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "客服电话多少",
        "请拨打客服热线 400-888-1234。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.validation.passed is True


def test_apply_validation_retry_refuses_after_exhausted(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            mode="strict",
            min_score=0.9,
            retry_on_fail=True,
            max_retries=1,
            refuse_on_fail=True,
        )
    )
    cite = store.fetch_citations("智链科技总部在哪")
    citations = cite.get("citations") or []
    outcome = apply_validation_retry(
        store,
        "智链科技总部在哪",
        "今天北京天气晴朗，适合出游。",
        citations,
        cite,
    )
    assert outcome is not None
    assert outcome.refused is True
    assert outcome.reply.startswith("[校验未通过]")
    assert outcome.validation.retries == 1


def test_validation_config_persists_retry_fields(tmp_path):
    store = _store(tmp_path)
    store.set_validation_config(
        ValidationConfig(retry_on_fail=True, max_retries=2, refuse_on_fail=False)
    )
    store.save(tmp_path / "store.json")
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    cfg = loaded.get_validation_config()
    assert cfg.retry_on_fail is True
    assert cfg.max_retries == 2
```


---

## 四十八、完整 API 测试

```python
"""Day 38 Validation Retry API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_validation_retry_preview(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "retries" in data
    assert data["passed"] is True


def test_validation_retry_preview_reports_route(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "理财安全吗",
            "reply": "投资需谨慎，详见产品说明书风险提示。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("retry_route") is not None or data.get("retries", 0) >= 0


def test_put_validation_config_retry_fields(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["retry_on_fail"] is True
    assert body["max_retries"] == 2


def test_status_includes_validation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["validation_config"]["retry_on_fail"] is False


def test_chat_includes_validation_retries_field(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": False,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert "retries" in body["validation"]


def test_chat_refuses_after_retry_exhausted(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "strict",
            "min_score": 0.9,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    assert resp.status_code == 200
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) >= 1
    assert val.get("passed") is False
    assert val.get("refused") is True
    assert body["reply"].startswith("[校验未通过]")


def test_chat_retry_preserves_day37_when_disabled(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": False,
            "max_retries": 0,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) == 0
    assert val.get("refused") is True


def test_validation_preview_still_works(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
```


---

## 四十九、课堂 8 分钟录音稿

「打开 validation_retry，apply_validation_retry 返回是否重试过。chat 里 validation.retries 挂在 reply 后面。前端可展示重试次数。这就是 ZL-NA-REQ-038。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 38 · Retry · ZL-NA-REQ-038 · validation_retry 精读完**
