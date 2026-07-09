# Day 36 精读：query_router 与自适应路由管线

**需求**：ZL-NA-REQ-036 | **学时**：120 min

---

## 一、query_router.py 全文

```python
"""
检索管线查询路由 — 意图分类 + expand/rewrite 开关

与 Day18 IntentRouter（Prompt 模板）正交：本模块决定**检索子管线**走哪条分支。

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.route_config import (
    INTENT_FAQ_FAST,
    INTENT_RAG_STANDARD,
    INTENT_RAG_WIDE,
    RouteConfig,
)

# (rule_id, pattern, intent, expand, rewrite)
DEFAULT_ROUTE_RULES: tuple[tuple[str, str, str, bool, bool], ...] = (
    (
        "faq_phone",
        r"电话|客服|联系|400-|热线",
        INTENT_FAQ_FAST,
        False,
        False,
    ),
    (
        "faq_upload",
        r"上传|pdf|文档怎么",
        INTENT_FAQ_FAST,
        False,
        True,
    ),
    (
        "wide_safety",
        r"安全吗|会不会亏|保本|合规",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "wide_risk",
        r"有风险吗|风险大吗|谨慎",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "standard_yield",
        r"年化|收益|赚多少|利率",
        INTENT_RAG_STANDARD,
        False,
        True,
    ),
)

INTENT_LABELS: dict[str, str] = {
    INTENT_FAQ_FAST: "FAQ 快路径 — 跳过 expand/rewrite",
    INTENT_RAG_STANDARD: "标准 RAG — rewrite，不 expand",
    INTENT_RAG_WIDE: "宽召回 — expand + rewrite",
}


@dataclass(frozen=True)
class RouteResult:
    """单条路由结果 — 供审计与 preview API"""

    original: str
    intent: str
    expand: bool
    rewrite: bool
    rule_id: str | None = None
    confidence: float = 0.0
    label: str = ""

    def to_dict(self) -> dict[str, str | bool | float | None]:
        return {
            "original": self.original,
            "intent": self.intent,
            "expand": self.expand,
            "rewrite": self.rewrite,
            "rule_id": self.rule_id,
            "confidence": round(self.confidence, 4),
            "label": self.label or INTENT_LABELS.get(self.intent, self.intent),
        }


class QueryRouter(ABC):
    """查询路由器抽象接口"""

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """将用户问句路由到检索子管线"""


class RuleBasedQueryRouter(QueryRouter):
    """
    规则表路由器 — 可审计、无 LLM 依赖

    命中第一条 regex 规则即返回对应 expand/rewrite 开关。
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str, bool, bool], ...] | None = None,
        config: RouteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ROUTE_RULES
        self._config = config or RouteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), intent, expand, rewrite)
            for rid, pat, intent, expand, rewrite in self._rules
        ]

    @property
    def config(self) -> RouteConfig:
        return self._config

    def route(self, query: str) -> RouteResult:
        original = (query or "").strip()
        if not original:
            return self._fallback("")

        for rid, pattern, intent, expand, rewrite in self._compiled:
            if pattern.search(original):
                return RouteResult(
                    original=original,
                    intent=intent,
                    expand=expand,
                    rewrite=rewrite,
                    rule_id=rid,
                    confidence=0.9,
                    label=INTENT_LABELS.get(intent, intent),
                )

        return self._fallback(original)

    def _fallback(self, original: str) -> RouteResult:
        intent = self._config.fallback_intent
        expand = intent == INTENT_RAG_WIDE
        rewrite = intent != INTENT_FAQ_FAST
        return RouteResult(
            original=original,
            intent=intent,
            expand=expand,
            rewrite=rewrite,
            rule_id=None,
            confidence=0.6,
            label=INTENT_LABELS.get(intent, intent),
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
检索管线路由配置 — 按意图动态开关 expand / rewrite

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"

INTENT_FAQ_FAST = "faq_fast"
INTENT_RAG_STANDARD = "rag_standard"
INTENT_RAG_WIDE = "rag_wide"


@dataclass
class RouteConfig:
    """RAG 检索管线路由策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_intent: str = INTENT_RAG_STANDARD

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        valid = {INTENT_FAQ_FAST, INTENT_RAG_STANDARD, INTENT_RAG_WIDE}
        if self.fallback_intent not in valid:
            raise ValueError(f"fallback_intent 无效: {self.fallback_intent!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_intent": self.fallback_intent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RouteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_intent=str(data.get("fallback_intent", INTENT_RAG_STANDARD)),
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
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import RoutingRetriever
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
    | RoutingRetriever
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
    if isinstance(retriever, RoutingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, RoutingRetriever):
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
检索管线路由配置 — 按意图动态开关 expand / rewrite

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"

INTENT_FAQ_FAST = "faq_fast"
INTENT_RAG_STANDARD = "rag_standard"
INTENT_RAG_WIDE = "rag_wide"


@dataclass
class RouteConfig:
    """RAG 检索管线路由策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_intent: str = INTENT_RAG_STANDARD

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        valid = {INTENT_FAQ_FAST, INTENT_RAG_STANDARD, INTENT_RAG_WIDE}
        if self.fallback_intent not in valid:
            raise ValueError(f"fallback_intent 无效: {self.fallback_intent!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_intent": self.fallback_intent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RouteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_intent=str(data.get("fallback_intent", INTENT_RAG_STANDARD)),
        )
```


`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

```python
def _build_rag_service(self) -> RAGContextService:
        if not self.chunks:
            return RAGContextService()

        from rag.embedding import EmbeddingClient
        from rag.retriever import KeywordRetriever

        client = EmbeddingClient()
        client.model.load_state(self.embedding_state)
        self._sync_chroma_from_json()
        chroma = self._chroma_index()
        vector = ChromaEmbeddingRetriever(self.chunks, chroma, client=client)
        keyword = KeywordRetriever(self.chunks)
        cfg = self.get_retrieval_config()
        hybrid = HybridRetriever(self.chunks, keyword, vector, config=cfg)
        rerank_cfg = self.get_rerank_config()
        reranking = RerankingRetriever(
            hybrid,
            reranker=MockCrossEncoderReranker(),
            config=rerank_cfg,
        )
        rewrite_cfg = self.get_rewrite_config()
        rewriting = RewritingRetriever(reranking, config=rewrite_cfg)
        expansion_cfg = self.get_expansion_config()
        expanding = RoutingRetriever(rewriting, config=expansion_cfg)
        route_cfg = self.get_route_config()
        retriever = RoutingRetriever(expanding, config=route_cfg)
        index = DocumentIndex(chunks=self.chunks, retriever=retriever)
        return RAGContextService(index)
```


`RAGContextService(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_query_router.py

```python
"""Day 36 查询路由单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.expanding_retriever import RoutingRetriever
from rag.knowledge_store import KnowledgeStore
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import INTENT_FAQ_FAST, INTENT_RAG_WIDE, RouteConfig
from rag.routing_retriever import RoutingRetriever


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_route_config_validate():
    RouteConfig().validate()
    with pytest.raises(ValueError):
        RouteConfig(fallback_intent="invalid").validate()


def test_router_faq_fast_skips_expand():
    route = RuleBasedQueryRouter().route("客服电话多少")
    assert route.intent == INTENT_FAQ_FAST
    assert route.expand is False
    assert route.rewrite is False


def test_router_wide_intent():
    route = RuleBasedQueryRouter().route("理财安全吗")
    assert route.intent == INTENT_RAG_WIDE
    assert route.expand is True
    assert route.rewrite is True


def test_router_standard_yield():
    route = RuleBasedQueryRouter().route("年化收益怎么样")
    assert route.expand is False
    assert route.rewrite is True


def test_routing_retriever_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_route_config(RouteConfig(enabled=False))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RoutingRetriever)
    hits = retriever.search("客服电话多少", top_k=2)
    assert hits
    assert retriever.last_route is not None


def test_routing_retriever_applies_fast_path(tmp_path):
    store = _store(tmp_path)
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RoutingRetriever)
    retriever.search("客服电话多少", top_k=2)
    assert retriever.last_route
    assert retriever.last_route.expand is False
    exp = retriever.inner
    assert isinstance(exp, RoutingRetriever)
    assert exp.last_expansion
    assert len(exp.last_expansion.queries) == 1


def test_fetch_citations_includes_route(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("客服电话多少")
    assert data.get("route")
    assert data["route"]["intent"] == INTENT_FAQ_FAST


def test_knowledge_store_persists_route_config(tmp_path):
    store = _store(tmp_path)
    store.set_route_config(RouteConfig(enabled=True, fallback_intent=INTENT_RAG_WIDE))
    store.save()
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    assert loaded.get_route_config().fallback_intent == INTENT_RAG_WIDE


def test_status_includes_route_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["platform_version"] == "0.39.0"
    assert status["route_config"]["enabled"] is True


def test_route_result_to_dict():
    route = RuleBasedQueryRouter().route("理财安全吗")
    data = route.to_dict()
    assert data["intent"] == INTENT_RAG_WIDE
    assert "label" in data


def test_routing_stack_outermost(tmp_path):
    store = _store(tmp_path)
    retriever = store.as_rag_service().index.retriever
    assert isinstance(retriever, RoutingRetriever)
    assert isinstance(retriever.inner, RoutingRetriever)
```


| 测试 | 要点 |
|------|------|
| test_query_router_classifies_intent_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_citation_preview_with_rewrite | 业务号码 |
| test_context_disabled | 降级路径 |
| test_fetch_citations_with_hits_accessible | inner 类型 |
| test_knowledge_store_persists_citation_config | 持久化 |

---

## 十一、API 测试 test_route_api.py

```python
"""Day 36 Route API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_get_route_config_default(client):
    data = client.get("/api/knowledge/route-config").json()
    assert data["enabled"] is True
    assert data["fallback_intent"] == "rag_standard"


def test_put_route_config(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "rag_wide",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fallback_intent"] == "rag_wide"


def test_route_preview_faq_fast(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "faq_fast"
    assert data["expand"] is False


def test_citation_preview_with_route(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("route")
    assert data["route"]["intent"] == "rag_wide"


def test_status_includes_route_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["route_config"]["enabled"] is True


def test_chat_includes_route(client):
    resp = client.post("/api/chat", json={"message": "客服电话多少？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("route")
    assert body["route"]["intent"] == "faq_fast"


def test_invalid_route_fallback_422(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "invalid",
        },
    )
    assert resp.status_code == 422


def test_route_preview_wide(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "会不会亏"},
    )
    assert resp.status_code == 200
    assert resp.json()["expand"] is True
```


`test_health_version` 锁版本 `v0.36.0`；`test_chat_includes_citations` 端到端。

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
def get_route_config(self) -> RouteConfig:
        return RouteConfig.from_dict(self.route_config.to_dict())

    def set_route_config(self, config: RouteConfig) -> RouteConfig:
        config.validate()
        self.route_config = RouteConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.route_config

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

    def validate_answer(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult | None:
        """按当前 validation_config 校验 reply 与 citations 一致性"""
        cfg = self.get_validation_config()
        if not cfg.enabled:
            return None
        validator = RuleBasedAnswerValidator(config=cfg)
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

读罢 22 精读，你应能**逐行**解释 `RuleBasedQueryRouter.route` 与 `RoutingRetriever.search`，并映射到 ZL-NA-REQ-036 的 FR-001–FR-003。

---

## 二十一、query_router 完整源码（重复嵌入便于打印）

```python
"""
检索管线查询路由 — 意图分类 + expand/rewrite 开关

与 Day18 IntentRouter（Prompt 模板）正交：本模块决定**检索子管线**走哪条分支。

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.route_config import (
    INTENT_FAQ_FAST,
    INTENT_RAG_STANDARD,
    INTENT_RAG_WIDE,
    RouteConfig,
)

# (rule_id, pattern, intent, expand, rewrite)
DEFAULT_ROUTE_RULES: tuple[tuple[str, str, str, bool, bool], ...] = (
    (
        "faq_phone",
        r"电话|客服|联系|400-|热线",
        INTENT_FAQ_FAST,
        False,
        False,
    ),
    (
        "faq_upload",
        r"上传|pdf|文档怎么",
        INTENT_FAQ_FAST,
        False,
        True,
    ),
    (
        "wide_safety",
        r"安全吗|会不会亏|保本|合规",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "wide_risk",
        r"有风险吗|风险大吗|谨慎",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "standard_yield",
        r"年化|收益|赚多少|利率",
        INTENT_RAG_STANDARD,
        False,
        True,
    ),
)

INTENT_LABELS: dict[str, str] = {
    INTENT_FAQ_FAST: "FAQ 快路径 — 跳过 expand/rewrite",
    INTENT_RAG_STANDARD: "标准 RAG — rewrite，不 expand",
    INTENT_RAG_WIDE: "宽召回 — expand + rewrite",
}


@dataclass(frozen=True)
class RouteResult:
    """单条路由结果 — 供审计与 preview API"""

    original: str
    intent: str
    expand: bool
    rewrite: bool
    rule_id: str | None = None
    confidence: float = 0.0
    label: str = ""

    def to_dict(self) -> dict[str, str | bool | float | None]:
        return {
            "original": self.original,
            "intent": self.intent,
            "expand": self.expand,
            "rewrite": self.rewrite,
            "rule_id": self.rule_id,
            "confidence": round(self.confidence, 4),
            "label": self.label or INTENT_LABELS.get(self.intent, self.intent),
        }


class QueryRouter(ABC):
    """查询路由器抽象接口"""

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """将用户问句路由到检索子管线"""


class RuleBasedQueryRouter(QueryRouter):
    """
    规则表路由器 — 可审计、无 LLM 依赖

    命中第一条 regex 规则即返回对应 expand/rewrite 开关。
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str, bool, bool], ...] | None = None,
        config: RouteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ROUTE_RULES
        self._config = config or RouteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), intent, expand, rewrite)
            for rid, pat, intent, expand, rewrite in self._rules
        ]

    @property
    def config(self) -> RouteConfig:
        return self._config

    def route(self, query: str) -> RouteResult:
        original = (query or "").strip()
        if not original:
            return self._fallback("")

        for rid, pattern, intent, expand, rewrite in self._compiled:
            if pattern.search(original):
                return RouteResult(
                    original=original,
                    intent=intent,
                    expand=expand,
                    rewrite=rewrite,
                    rule_id=rid,
                    confidence=0.9,
                    label=INTENT_LABELS.get(intent, intent),
                )

        return self._fallback(original)

    def _fallback(self, original: str) -> RouteResult:
        intent = self._config.fallback_intent
        expand = intent == INTENT_RAG_WIDE
        rewrite = intent != INTENT_FAQ_FAST
        return RouteResult(
            original=original,
            intent=intent,
            expand=expand,
            rewrite=rewrite,
            rule_id=None,
            confidence=0.6,
            label=INTENT_LABELS.get(intent, intent),
        )
```


---

## 二十二、自适应路由伪代码

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
| test_query_router_classifies_intent_candidates | FR-002 |
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

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-036 / ZL-NA-REQ-036 / ZL-NA-REQ-037 / ZL-NA-REQ-038
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
    RouteConfigRequest,
    RouteConfigResponse,
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
from rag.expansion_config import RouteConfig
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

课后运行 `src/day36/phase3_route_review.py` 串联 Day25–34。

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
5. 能 curl GET route-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 route_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 20 tests  
10. 能解释翻牌测试  
11. 能对比 Day33  
12. 能预告 Day35 HyDE  
13. 能读 validate 源码  
14. 能解释 include_route_meta  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_citations 上限 10  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-036 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`fetch_citations` 是 **Facade**：对外返回 dict，对内调用 RoutingRetriever.search。与 Day33 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 36 Route API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_get_route_config_default(client):
    data = client.get("/api/knowledge/route-config").json()
    assert data["enabled"] is True
    assert data["fallback_intent"] == "rag_standard"


def test_put_route_config(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "rag_wide",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fallback_intent"] == "rag_wide"


def test_route_preview_faq_fast(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "faq_fast"
    assert data["expand"] is False


def test_citation_preview_with_route(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("route")
    assert data["route"]["intent"] == "rag_wide"


def test_status_includes_route_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["route_config"]["enabled"] is True


def test_chat_includes_route(client):
    resp = client.post("/api/chat", json={"message": "客服电话多少？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("route")
    assert body["route"]["intent"] == "faq_fast"


def test_invalid_route_fallback_422(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "invalid",
        },
    )
    assert resp.status_code == 422


def test_route_preview_wide(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "会不会亏"},
    )
    assert resp.status_code == 200
    assert resp.json()["expand"] is True
```


---

## 三十一、课堂录音稿（8 min）

「打开 context，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，citation_builder 逐对 rewrite，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RAGContextService + RouteConfig
- GET/PUT /api/knowledge/route-config
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
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import RoutingRetriever
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
    | RoutingRetriever
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
    if isinstance(retriever, RoutingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, RoutingRetriever):
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
检索管线路由演示 — 意图 → expand/rewrite 开关

运行：PYTHONPATH=src python3 src/day36/route_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day36.constants import ROUTE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.query_router import RuleBasedQueryRouter


def main() -> int:
    print("=" * 60)
    print("  Day 36 Query Router 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_route_config()
    router = RuleBasedQueryRouter(config=cfg)
    print(f"\n  route enabled={cfg.enabled} fallback={cfg.fallback_intent}")

    for item in ROUTE_QUERIES:
        q = item["query"]
        route = router.route(q)
        print(f"\n  Q: {q}")
        print(f"    intent={route.intent} expand={route.expand} rewrite={route.rewrite}")
        print(f"    label: {route.label}")
        data = store.fetch_citations(q)
        if data.get("route"):
            print(f"    routed expand={data['route']['expand']}")

    print("\n  ✅ Route 演示完成")
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

## 四十、query_router 全文嵌入

```python
"""
检索管线查询路由 — 意图分类 + expand/rewrite 开关

与 Day18 IntentRouter（Prompt 模板）正交：本模块决定**检索子管线**走哪条分支。

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.route_config import (
    INTENT_FAQ_FAST,
    INTENT_RAG_STANDARD,
    INTENT_RAG_WIDE,
    RouteConfig,
)

# (rule_id, pattern, intent, expand, rewrite)
DEFAULT_ROUTE_RULES: tuple[tuple[str, str, str, bool, bool], ...] = (
    (
        "faq_phone",
        r"电话|客服|联系|400-|热线",
        INTENT_FAQ_FAST,
        False,
        False,
    ),
    (
        "faq_upload",
        r"上传|pdf|文档怎么",
        INTENT_FAQ_FAST,
        False,
        True,
    ),
    (
        "wide_safety",
        r"安全吗|会不会亏|保本|合规",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "wide_risk",
        r"有风险吗|风险大吗|谨慎",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "standard_yield",
        r"年化|收益|赚多少|利率",
        INTENT_RAG_STANDARD,
        False,
        True,
    ),
)

INTENT_LABELS: dict[str, str] = {
    INTENT_FAQ_FAST: "FAQ 快路径 — 跳过 expand/rewrite",
    INTENT_RAG_STANDARD: "标准 RAG — rewrite，不 expand",
    INTENT_RAG_WIDE: "宽召回 — expand + rewrite",
}


@dataclass(frozen=True)
class RouteResult:
    """单条路由结果 — 供审计与 preview API"""

    original: str
    intent: str
    expand: bool
    rewrite: bool
    rule_id: str | None = None
    confidence: float = 0.0
    label: str = ""

    def to_dict(self) -> dict[str, str | bool | float | None]:
        return {
            "original": self.original,
            "intent": self.intent,
            "expand": self.expand,
            "rewrite": self.rewrite,
            "rule_id": self.rule_id,
            "confidence": round(self.confidence, 4),
            "label": self.label or INTENT_LABELS.get(self.intent, self.intent),
        }


class QueryRouter(ABC):
    """查询路由器抽象接口"""

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """将用户问句路由到检索子管线"""


class RuleBasedQueryRouter(QueryRouter):
    """
    规则表路由器 — 可审计、无 LLM 依赖

    命中第一条 regex 规则即返回对应 expand/rewrite 开关。
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str, bool, bool], ...] | None = None,
        config: RouteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ROUTE_RULES
        self._config = config or RouteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), intent, expand, rewrite)
            for rid, pat, intent, expand, rewrite in self._rules
        ]

    @property
    def config(self) -> RouteConfig:
        return self._config

    def route(self, query: str) -> RouteResult:
        original = (query or "").strip()
        if not original:
            return self._fallback("")

        for rid, pattern, intent, expand, rewrite in self._compiled:
            if pattern.search(original):
                return RouteResult(
                    original=original,
                    intent=intent,
                    expand=expand,
                    rewrite=rewrite,
                    rule_id=rid,
                    confidence=0.9,
                    label=INTENT_LABELS.get(intent, intent),
                )

        return self._fallback(original)

    def _fallback(self, original: str) -> RouteResult:
        intent = self._config.fallback_intent
        expand = intent == INTENT_RAG_WIDE
        rewrite = intent != INTENT_FAQ_FAST
        return RouteResult(
            original=original,
            intent=intent,
            expand=expand,
            rewrite=rewrite,
            rule_id=None,
            confidence=0.6,
            label=INTENT_LABELS.get(intent, intent),
        )
```


---

## 四十一、chat citations 代码

```python

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
| test_query_router_classifies_intent | FR-002 |
| test_fetch_citations_with_hits | FR-003 |
| test_chat_includes_citations | FR-006 |
| test_citation_preview_with_rewrite | FR-005 |

---

## 四十六、完整 context.py 引用段

```python

```


---

## 四十七、完整测试文件

```python
"""Day 36 查询路由单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.expanding_retriever import RoutingRetriever
from rag.knowledge_store import KnowledgeStore
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import INTENT_FAQ_FAST, INTENT_RAG_WIDE, RouteConfig
from rag.routing_retriever import RoutingRetriever


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_route_config_validate():
    RouteConfig().validate()
    with pytest.raises(ValueError):
        RouteConfig(fallback_intent="invalid").validate()


def test_router_faq_fast_skips_expand():
    route = RuleBasedQueryRouter().route("客服电话多少")
    assert route.intent == INTENT_FAQ_FAST
    assert route.expand is False
    assert route.rewrite is False


def test_router_wide_intent():
    route = RuleBasedQueryRouter().route("理财安全吗")
    assert route.intent == INTENT_RAG_WIDE
    assert route.expand is True
    assert route.rewrite is True


def test_router_standard_yield():
    route = RuleBasedQueryRouter().route("年化收益怎么样")
    assert route.expand is False
    assert route.rewrite is True


def test_routing_retriever_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_route_config(RouteConfig(enabled=False))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RoutingRetriever)
    hits = retriever.search("客服电话多少", top_k=2)
    assert hits
    assert retriever.last_route is not None


def test_routing_retriever_applies_fast_path(tmp_path):
    store = _store(tmp_path)
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RoutingRetriever)
    retriever.search("客服电话多少", top_k=2)
    assert retriever.last_route
    assert retriever.last_route.expand is False
    exp = retriever.inner
    assert isinstance(exp, RoutingRetriever)
    assert exp.last_expansion
    assert len(exp.last_expansion.queries) == 1


def test_fetch_citations_includes_route(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("客服电话多少")
    assert data.get("route")
    assert data["route"]["intent"] == INTENT_FAQ_FAST


def test_knowledge_store_persists_route_config(tmp_path):
    store = _store(tmp_path)
    store.set_route_config(RouteConfig(enabled=True, fallback_intent=INTENT_RAG_WIDE))
    store.save()
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    assert loaded.get_route_config().fallback_intent == INTENT_RAG_WIDE


def test_status_includes_route_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["platform_version"] == "0.39.0"
    assert status["route_config"]["enabled"] is True


def test_route_result_to_dict():
    route = RuleBasedQueryRouter().route("理财安全吗")
    data = route.to_dict()
    assert data["intent"] == INTENT_RAG_WIDE
    assert "label" in data


def test_routing_stack_outermost(tmp_path):
    store = _store(tmp_path)
    retriever = store.as_rag_service().index.retriever
    assert isinstance(retriever, RoutingRetriever)
    assert isinstance(retriever.inner, RoutingRetriever)
```


---

## 四十八、完整 API 测试

```python
"""Day 36 Route API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_get_route_config_default(client):
    data = client.get("/api/knowledge/route-config").json()
    assert data["enabled"] is True
    assert data["fallback_intent"] == "rag_standard"


def test_put_route_config(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "rag_wide",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fallback_intent"] == "rag_wide"


def test_route_preview_faq_fast(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "faq_fast"
    assert data["expand"] is False


def test_citation_preview_with_route(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("route")
    assert data["route"]["intent"] == "rag_wide"


def test_status_includes_route_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["route_config"]["enabled"] is True


def test_chat_includes_route(client):
    resp = client.post("/api/chat", json={"message": "客服电话多少？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("route")
    assert body["route"]["intent"] == "faq_fast"


def test_invalid_route_fallback_422(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "invalid",
        },
    )
    assert resp.status_code == 422


def test_route_preview_wide(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "会不会亏"},
    )
    assert resp.status_code == 200
    assert resp.json()["expand"] is True
```


---

## 四十九、课堂 8 分钟录音稿

「打开 query_router，RouteDecision 有 intent chunk_id source score preview。chat 里 fetch_citations 挂在 reply 后面。前端 citations 数组渲染来源。这就是 ZL-NA-REQ-036。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 37 · Citation · ZL-NA-REQ-036 · query_router 精读完**
