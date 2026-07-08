# Day 33 精读：rewriteer 与三阶段检索管线

**需求**：ZL-NA-REQ-033 | **学时**：120 min

---

## 一、rewriteer.py 全文

```python
"""
查询改写 — 口语问句规范化为检索友好 query

RuleBasedQueryRewriter 用可审计规则表将指代、口语映射为
与 sample_docs 对齐的关键词（年化收益率、联系方式、投资风险等）。

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.rewrite_config import RewriteConfig

# (rule_id, pattern, replacement) — 顺序优先，先匹配先应用
DEFAULT_RULES: tuple[tuple[str, str, str], ...] = (
    ("colloquial_yield", r"那个.{0,12}理财.{0,8}赚", "年化收益率是多少"),
    ("colloquial_yield_short", r"能赚多少|收益怎么样|赚多少", "年化收益率"),
    ("annual_yield", r"年化.{0,4}多少|收益率.{0,4}多少", "年化收益率可达"),
    ("risk_colloquial", r"有风险吗|会不会亏|安全吗", "投资有风险"),
    ("contact_phone", r"客服.{0,6}电话|联系电话|怎么联系|电话多少", "联系方式客服电话"),
    ("manager_phone", r"客户经理.{0,4}手机", "客户经理手机"),
    ("internal_doc", r"内部资料|保密", "内部资料禁止外传"),
    ("pdf_upload", r"怎么上传.{0,6}pdf|pdf.{0,6}上传", "如何上传PDF文档"),
)


@dataclass(frozen=True)
class RewriteResult:
    """单条改写结果 — 供审计与 preview API"""

    original: str
    rewritten: str
    changed: bool
    rule_id: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "original": self.original,
            "rewritten": self.rewritten,
            "changed": self.changed,
            "rule_id": self.rule_id,
        }


class QueryRewriter(ABC):
    """查询改写器抽象接口"""

    @abstractmethod
    def rewrite(self, query: str) -> RewriteResult:
        """将用户问句改写为检索 query"""


class RuleBasedQueryRewriter(QueryRewriter):
    """
    规则表改写器 — 可审计、无 LLM 依赖

    流程：normalize → 逐条 regex 匹配 → 命中则替换并截断长度
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str], ...] | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_RULES
        self._config = config or RewriteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), repl)
            for rid, pat, repl in self._rules
        ]

    @property
    def config(self) -> RewriteConfig:
        return self._config

    def rewrite(self, query: str) -> RewriteResult:
        original = (query or "").strip()
        if not original:
            return RewriteResult(original="", rewritten="", changed=False)

        text = _normalize_query(original)
        rule_id: str | None = None

        for rid, pattern, replacement in self._compiled:
            if pattern.search(text):
                text = replacement
                rule_id = rid
                break

        text = text[: self._config.max_rewrite_len].strip()
        if not text and self._config.fallback_to_original:
            text = original

        changed = text != original
        return RewriteResult(
            original=original,
            rewritten=text,
            changed=changed,
            rule_id=rule_id,
        )


def _normalize_query(text: str) -> str:
    """全角空格、连续空白压缩"""
    t = text.replace("\u3000", " ").strip()
    t = re.sub(r"\s+", " ", t)
    return t
```


---

## 二、行级注释：Rewriteer 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rewrite(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、RuleBasedQueryRewriter（L33–L68）

```python
class RuleBasedQueryRewriter(QueryRewriter):
    """
    规则表改写器 — 可审计、无 LLM 依赖

    流程：normalize → 逐条 regex 匹配 → 命中则替换并截断长度
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str], ...] | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_RULES
        self._config = config or RewriteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), repl)
            for rid, pat, repl in self._rules
        ]

    @property
    def config(self) -> RewriteConfig:
        return self._config

    def rewrite(self, query: str) -> RewriteResult:
        original = (query or "").strip()
        if not original:
            return RewriteResult(original="", rewritten="", changed=False)

        text = _normalize_query(original)
        rule_id: str | None = None

        for rid, pattern, replacement in self._compiled:
            if pattern.search(text):
                text = replacement
                rule_id = rid
                break

        text = text[: self._config.max_rewrite_len].strip()
        if not text and self._config.fallback_to_original:
            text = original

        changed = text != original
        return RewriteResult(
            original=original,
            rewritten=text,
            changed=changed,
            rule_id=rule_id,
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
DEFAULT_RULES: tuple[tuple[str, str, str], ...] = (
    ("colloquial_yield", r"那个.{0,12}理财.{0,8}赚", "年化收益率是多少"),
    ("colloquial_yield_short", r"能赚多少|收益怎么样|赚多少", "年化收益率"),
    ("annual_yield", r"年化.{0,4}多少|收益率.{0,4}多少", "年化收益率可达"),
    ("risk_colloquial", r"有风险吗|会不会亏|安全吗", "投资有风险"),
    ("contact_phone", r"客服.{0,6}电话|联系电话|怎么联系|电话多少", "联系方式客服电话"),
    ("manager_phone", r"客户经理.{0,4}手机", "客户经理手机"),
    ("internal_doc", r"内部资料|保密", "内部资料禁止外传"),
    ("pdf_upload", r"怎么上传.{0,6}pdf|pdf.{0,6}上传", "如何上传PDF文档"),
)


@dataclass(frozen=True)
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
DEFAULT_RULES: tuple[tuple[str, str, str], ...] = (
    ("colloquial_yield", r"那个.{0,12}理财.{0,8}赚", "年化收益率是多少"),
    ("colloquial_yield_short", r"能赚多少|收益怎么样|赚多少", "年化收益率"),
    ("annual_yield", r"年化.{0,4}多少|收益率.{0,4}多少", "年化收益率可达"),
    ("risk_colloquial", r"有风险吗|会不会亏|安全吗", "投资有风险"),
    ("contact_phone", r"客服.{0,6}电话|联系电话|怎么联系|电话多少", "联系方式客服电话"),
    ("manager_phone", r"客户经理.{0,4}手机", "客户经理手机"),
    ("internal_doc", r"内部资料|保密", "内部资料禁止外传"),
    ("pdf_upload", r"怎么上传.{0,6}pdf|pdf.{0,6}上传", "如何上传PDF文档"),
)


@dataclass(frozen=True)
```


中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、rewriteing_retriever.py 全文

```python
"""
Rewriting 检索管线 — 查询改写 → hybrid → rerank

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from rag.query_rewriter import QueryRewriter, RewriteResult, RuleBasedQueryRewriter
from rag.rewrite_config import RewriteConfig
from rag.retriever import RetrievalResult


class RewritingRetriever:
    """
    最外层检索装饰器 — 先改写 query，再委托内层检索

    典型用法：
        inner = RerankingRetriever(HybridRetriever(...))
        retriever = RewritingRetriever(inner, config=RewriteConfig())
        hits = retriever.search("那个理财能赚多少", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        rewriter: QueryRewriter | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._inner = inner
        self._config = config or RewriteConfig()
        self._rewriter = rewriter or RuleBasedQueryRewriter(config=self._config)
        self._last_rewrite: RewriteResult | None = None

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RewriteConfig:
        return self._config

    @property
    def last_rewrite(self) -> RewriteResult | None:
        """最近一次 search 的改写结果（演示 / 审计）"""
        return self._last_rewrite

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_rewrite = None
            return []

        cfg = self._config
        if not cfg.enabled:
            self._last_rewrite = RewriteResult(
                original=query, rewritten=query, changed=False
            )
            return self._inner.search(query, top_k=top_k)

        result = self._rewriter.rewrite(query)
        self._last_rewrite = result
        search_q = result.rewritten or query
        return self._inner.search(search_q, top_k=top_k)
```


---

## 七、search 主流程

```python
def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_rewrite = None
            return []
```


| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rewrite 开销 |
| pool 计算 | `max(max_rewrite_len, top_k)` |
| candidates | inner hybrid 宽召回 |
| rewrite 调用 | MockCrossEncoder 改写截断 |

---

## 八、rewrite_config.py 全文

```python
"""
查询改写配置 — 开关、模式与回退策略

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"


@dataclass
class RewriteConfig:
    """检索前查询改写策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_to_original: bool = True
    max_rewrite_len: int = 200

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        if self.max_rewrite_len < 10:
            raise ValueError("max_rewrite_len 须 >= 10")
        if self.max_rewrite_len > 500:
            raise ValueError("max_rewrite_len 须 <= 500")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_to_original": self.fallback_to_original,
            "max_rewrite_len": self.max_rewrite_len,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RewriteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_to_original=bool(data.get("fallback_to_original", True)),
            max_rewrite_len=int(data.get("max_rewrite_len", 200)),
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
        retriever = RewritingRetriever(reranking, config=rewrite_cfg)
        index = DocumentIndex(chunks=self.chunks, retriever=retriever)
        return RAGContextService(index)
```


`RewritingRetriever(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_rewriteer.py

```python
"""Day 33 Query Rewrite 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.hybrid_retriever import HybridRetriever
from rag.knowledge_store import KnowledgeStore
from rag.query_rewriter import RuleBasedQueryRewriter
from rag.reranking_retriever import RerankingRetriever
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _get_rewriting(store: KnowledgeStore) -> RewritingRetriever:
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RewritingRetriever)
    return retriever


def test_rewrite_config_validate():
    RewriteConfig().validate()
    with pytest.raises(ValueError):
        RewriteConfig(mode="llm").validate()
    with pytest.raises(ValueError):
        RewriteConfig(max_rewrite_len=5).validate()


def test_rule_rewrite_colloquial_yield():
    r = RuleBasedQueryRewriter().rewrite("那个理财能赚多少")
    assert r.changed
    assert "年化" in r.rewritten
    assert r.rule_id is not None


def test_rule_rewrite_risk():
    r = RuleBasedQueryRewriter().rewrite("有风险吗")
    assert r.changed
    assert "风险" in r.rewritten


def test_rule_rewrite_contact():
    r = RuleBasedQueryRewriter().rewrite("客服电话多少")
    assert r.changed
    assert "联系" in r.rewritten or "电话" in r.rewritten


def test_rewrite_unchanged_passthrough():
    r = RuleBasedQueryRewriter().rewrite("年化收益率可达")
    assert r.rewritten == "年化收益率可达"
    assert r.changed is False


def test_rewriting_retriever_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_rewrite_config(RewriteConfig(enabled=False))
    w = _get_rewriting(store)
    hits = w.search("那个理财能赚多少", top_k=2)
    assert hits
    assert w.last_rewrite is not None
    assert w.last_rewrite.changed is False


def test_rewriting_retriever_enabled_search(tmp_path):
    store = _store(tmp_path)
    store.set_rewrite_config(RewriteConfig(enabled=True))
    w = _get_rewriting(store)
    hits = w.search("那个理财能赚多少", top_k=2)
    assert hits
    assert w.last_rewrite is not None
    assert w.last_rewrite.changed is True
    assert "年化" in w.last_rewrite.rewritten


def test_colloquial_query_finds_yield_chunk(tmp_path):
    store = _store(tmp_path)
    store.set_rewrite_config(RewriteConfig(enabled=True))
    w = _get_rewriting(store)
    hits = w.search("那个理财能赚多少", top_k=1)
    assert hits
    text = hits[0].chunk.text
    assert "8%" in text or "年化" in text


def test_knowledge_store_persists_rewrite_config(tmp_path):
    path = tmp_path / "persist.json"
    store = _store(tmp_path)
    store.store_path = path
    store.set_rewrite_config(RewriteConfig(enabled=False, max_rewrite_len=150))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_rewrite_config()
    assert cfg.enabled is False
    assert cfg.max_rewrite_len == 150


def test_status_includes_rewrite_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["rewrite_config"]["enabled"] is True
    assert status["rewrite_config"]["mode"] == "rules"


def test_inner_reranking_accessible(tmp_path):
    store = _store(tmp_path)
    w = _get_rewriting(store)
    assert isinstance(w.inner, RerankingRetriever)
    assert isinstance(w.inner.inner, HybridRetriever)


def test_fallback_to_original_on_empty():
    cfg = RewriteConfig(fallback_to_original=True, max_rewrite_len=10)
    r = RuleBasedQueryRewriter(config=cfg).rewrite("x" * 20)
    assert r.rewritten
```


| 测试 | 要点 |
|------|------|
| test_mock_rewrite_reorders_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_phone_query_rewrite | 业务号码 |
| test_rewriteing_retriever_disabled | 降级路径 |
| test_inner_hybrid_accessible | inner 类型 |
| test_knowledge_store_persists_rewrite_config | 持久化 |

---

## 十一、API 测试 test_rewrite_api.py

```python
"""Day 33 Query Rewrite API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.34.0"


def test_get_rewrite_config_default(client):
    data = client.get("/api/knowledge/rewrite-config").json()
    assert data["enabled"] is True
    assert data["mode"] == "rules"


def test_put_rewrite_config_disable(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": False,
            "mode": "rules",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_rewrite_preview_colloquial(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "那个理财能赚多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["changed"] is True
    assert "年化" in data["rewritten"]


def test_status_includes_rewrite_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.34.0"
    assert status["rewrite_config"]["enabled"] is True


def test_invalid_rewrite_mode_422(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": True,
            "mode": "llm",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 422


def test_chat_with_rewrite(client):
    resp = client.post("/api/chat", json={"message": "那个理财能赚多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_rewrite_preview_unchanged(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "年化收益率可达"},
    )
    assert resp.status_code == 200
    assert resp.json()["changed"] is False
```


`test_health_version` 锁版本 `v0.33.0`；`test_chat_with_rewrite` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rewrite 后前 3 的 rewrite  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json rewrite_config  

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

## 十五、与 Day32 衔接

HybridRetriever 仍是 inner；关 rewrite 即回 Day32 行为。retrieval_config 与 rewrite_config 正交。

---

## 十六、knowledge_store rewrite 方法

```python
def get_rewrite_config(self) -> RewriteConfig:
        return RewriteConfig.from_dict(self.rewrite_config.to_dict())

    def set_rewrite_config(self, config: RewriteConfig) -> RewriteConfig:
        config.validate()
        self.rewrite_config = RewriteConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.rewrite_config

    def get_citation_config(self) -> CitationConfig:
        return CitationConfig.from_dict(self.citation_config.to_dict())

    def set_citation_config(self, config: CitationConfig) -> CitationConfig:
        config.validate()
        self.citation_config = CitationConfig.from_dict(config.to_dict())
        return self.citation_config

    def fetch_citations(self, query: str) -> dict[str, Any]:
        """按当前 citation_config 检索并返回引用包 dict"""
        cfg = self.get_citation_config()
        if not cfg.enabled:
            return {"query": query.strip(), "citations": [], "rewrite": None}
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(query, config=cfg)
        return bundle.to_dict()

    def ingest_text(
        self,
        content: str,
        *,
        filename: str,
        clean: bool = True,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeDocument:
        """将文本写入知识库并重建索引"""
        cfg = self.get_chunk_config()
        cs = chunk_size if chunk_size is not None else cfg.chunk_size
        ov = overlap if overlap is not None else cfg.overlap
        text = (content or "").strip()
        if not text:
            raise ValueError("文档内容不能为空")
        if not filename.strip():
            raise ValueError("filename 不能为空")

        cleaned = text
        if clean:
            cleaned, _ = clean_text(text)
        doc = DocumentRecord(
            path=Path(filename),
            content=text,
            encoding="utf-8",
            size_bytes=len(text.encode("utf-8")),
            cleaned=cleaned,
        )
        new_chunks = chunk_documents(
            [doc],
            chunk_size=cs,
            overlap=ov,
            use_cleaned=clean,
        )
        self._append_chunks(filename, new_chunks, size_bytes=doc.size_bytes)
        self._rebuild_index()
        return self.documents[-1]

    def ingest_file(
        self,
        path: Path,
        *,
        clean: bool = True,
        chunk_size: int = 200,
        overlap: int = 40,
    ) -> KnowledgeDocument:
        """从磁盘文件 ingestion"""
        content, encoding = read_text_file(path)
        cleaned = content
        if clean:
            cleaned, _ = clean_text(content)
        doc = DocumentRecord(
            path=path,
            content=content,
            encoding=encoding,
            size_bytes=path.stat().st_size,
            cleaned=cleaned,
        )
        new_chunks = chunk_documents(
            [doc],
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=clean,
        )
        self._append_chunks(path.name, new_chunks, size_bytes=doc.size_bytes)
        self._rebuild_index()
        return self.documents[-1]
```


`set_rewrite_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rewrite 是什么。  
2. 1 分钟对比召回与改写。  
3. 白板画 RewritingRetriever.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q 能否 async batch rewrite？** 可优化；当前同步教学实现。  
**Q matched_tokens 会变吗？** rewrite 保留原 matched_tokens，只换 score。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RewritingRetriever.search` 与 `rewrite`，并映射到 ZL-NA-REQ-033 的 FR-001–FR-003。

---

## 二十一、rewriteer 完整源码（重复嵌入便于打印）

```python
"""
查询改写 — 口语问句规范化为检索友好 query

RuleBasedQueryRewriter 用可审计规则表将指代、口语映射为
与 sample_docs 对齐的关键词（年化收益率、联系方式、投资风险等）。

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.rewrite_config import RewriteConfig

# (rule_id, pattern, replacement) — 顺序优先，先匹配先应用
DEFAULT_RULES: tuple[tuple[str, str, str], ...] = (
    ("colloquial_yield", r"那个.{0,12}理财.{0,8}赚", "年化收益率是多少"),
    ("colloquial_yield_short", r"能赚多少|收益怎么样|赚多少", "年化收益率"),
    ("annual_yield", r"年化.{0,4}多少|收益率.{0,4}多少", "年化收益率可达"),
    ("risk_colloquial", r"有风险吗|会不会亏|安全吗", "投资有风险"),
    ("contact_phone", r"客服.{0,6}电话|联系电话|怎么联系|电话多少", "联系方式客服电话"),
    ("manager_phone", r"客户经理.{0,4}手机", "客户经理手机"),
    ("internal_doc", r"内部资料|保密", "内部资料禁止外传"),
    ("pdf_upload", r"怎么上传.{0,6}pdf|pdf.{0,6}上传", "如何上传PDF文档"),
)


@dataclass(frozen=True)
class RewriteResult:
    """单条改写结果 — 供审计与 preview API"""

    original: str
    rewritten: str
    changed: bool
    rule_id: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "original": self.original,
            "rewritten": self.rewritten,
            "changed": self.changed,
            "rule_id": self.rule_id,
        }


class QueryRewriter(ABC):
    """查询改写器抽象接口"""

    @abstractmethod
    def rewrite(self, query: str) -> RewriteResult:
        """将用户问句改写为检索 query"""


class RuleBasedQueryRewriter(QueryRewriter):
    """
    规则表改写器 — 可审计、无 LLM 依赖

    流程：normalize → 逐条 regex 匹配 → 命中则替换并截断长度
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str], ...] | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_RULES
        self._config = config or RewriteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), repl)
            for rid, pat, repl in self._rules
        ]

    @property
    def config(self) -> RewriteConfig:
        return self._config

    def rewrite(self, query: str) -> RewriteResult:
        original = (query or "").strip()
        if not original:
            return RewriteResult(original="", rewritten="", changed=False)

        text = _normalize_query(original)
        rule_id: str | None = None

        for rid, pattern, replacement in self._compiled:
            if pattern.search(text):
                text = replacement
                rule_id = rid
                break

        text = text[: self._config.max_rewrite_len].strip()
        if not text and self._config.fallback_to_original:
            text = original

        changed = text != original
        return RewriteResult(
            original=original,
            rewritten=text,
            changed=changed,
            rule_id=rule_id,
        )


def _normalize_query(text: str) -> str:
    """全角空格、连续空白压缩"""
    t = text.replace("\u3000", " ").strip()
    t = re.sub(r"\s+", " ", t)
    return t
```


---

## 二十二、三阶段伪代码

```
function RERANKING_SEARCH(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(max_rewrite_len, top_k)
    C = INNER(q, P)          # HybridRetriever
    return RERANK(q, C, top_k)
```

---

## 二十三、RERANK_QUERIES 业务解读

| query | 业务意图 | rewrite 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_rewrite_config_validate | FR-004 |
| test_mock_rewrite_reorders_candidates | FR-002 |
| test_rewriteing_retriever_enabled | FR-003 |
| test_phone_query_rewrite | AC-03 |
| test_knowledge_store_persists_rewrite_config | FR-005 |
| test_health_version | FR-008 |
| test_put_rewrite_config_disable | AC-02 |
| test_chat_with_rewrite | AC-05 |

---

## 二十五、knowledge API 节选（rewrite 上下文）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034
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
from rag.query_rewriter import RuleBasedQueryRewriter
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


@router.post("/citation-preview", response_model=CitationPreviewResponse)
def citation_preview(body: CitationPreviewRequest) -> CitationPreviewResponse:
    """预览单条 query 的检索引用（含 rewrite 审计）"""
    store = get_knowledge_store()
    data = store.fetch_citations(body.query)
    return CitationPreviewResponse(**data)


@router.get("/chunk-config", response_model=ChunkConfigResponse)
def get_chunk_config() -> ChunkConfigResponse:
    """返回当前知识库默认分块参数"""
    cfg = get_knowledge_store().get_chunk_config()
    return ChunkConfigResponse(**cfg.to_dict())


@router.put("/chunk-config", response_model=ChunkConfigResponse)
def update_chunk_config(body: ChunkConfigRequest) -> ChunkConfigResponse:
    """更新默认分块参数（影
```


---

## 二十六、phase3_rewrite_review 建议

课后运行 `src/day34/phase3_rewrite_review.py` 串联 Day25–32。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| rewrite 替代 hybrid | 外包层 |
| hybrid 分与 rewrite 分可比 | 仅排序 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 rewrite 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET rewrite-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 rewrite_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 18 tests  
10. 能解释翻牌测试  
11. 能对比 Day32  
12. 能预告 Day34 rewrite  
13. 能读 validate 源码  
14. 能解释 inner 属性  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_rewrite_len 上限 100  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-033 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`RewritingRetriever` 是 **Decorator**：对外统一 `search`，对内委托 `HybridRetriever`。与 Day32 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 33 Query Rewrite API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.34.0"


def test_get_rewrite_config_default(client):
    data = client.get("/api/knowledge/rewrite-config").json()
    assert data["enabled"] is True
    assert data["mode"] == "rules"


def test_put_rewrite_config_disable(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": False,
            "mode": "rules",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_rewrite_preview_colloquial(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "那个理财能赚多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["changed"] is True
    assert "年化" in data["rewritten"]


def test_status_includes_rewrite_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.34.0"
    assert status["rewrite_config"]["enabled"] is True


def test_invalid_rewrite_mode_422(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": True,
            "mode": "llm",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 422


def test_chat_with_rewrite(client):
    resp = client.post("/api/chat", json={"message": "那个理财能赚多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_rewrite_preview_unchanged(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "年化收益率可达"},
    )
    assert resp.status_code == 200
    assert resp.json()["changed"] is False
```


---

## 三十一、课堂录音稿（8 min）

「打开 rewriteing_retriever，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，rewriteer 逐对 rewrite，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RewritingRetriever + RewriteConfig
- GET/PUT /api/knowledge/rewrite-config
- tests/day34 (18 cases)
```

---

## 三十三、rewriteing_retriever 二次嵌入

```python
"""
Rewriting 检索管线 — 查询改写 → hybrid → rerank

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from rag.query_rewriter import QueryRewriter, RewriteResult, RuleBasedQueryRewriter
from rag.rewrite_config import RewriteConfig
from rag.retriever import RetrievalResult


class RewritingRetriever:
    """
    最外层检索装饰器 — 先改写 query，再委托内层检索

    典型用法：
        inner = RerankingRetriever(HybridRetriever(...))
        retriever = RewritingRetriever(inner, config=RewriteConfig())
        hits = retriever.search("那个理财能赚多少", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        rewriter: QueryRewriter | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._inner = inner
        self._config = config or RewriteConfig()
        self._rewriter = rewriter or RuleBasedQueryRewriter(config=self._config)
        self._last_rewrite: RewriteResult | None = None

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RewriteConfig:
        return self._config

    @property
    def last_rewrite(self) -> RewriteResult | None:
        """最近一次 search 的改写结果（演示 / 审计）"""
        return self._last_rewrite

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_rewrite = None
            return []

        cfg = self._config
        if not cfg.enabled:
            self._last_rewrite = RewriteResult(
                original=query, rewritten=query, changed=False
            )
            return self._inner.search(query, top_k=top_k)

        result = self._rewriter.rewrite(query)
        self._last_rewrite = result
        search_q = result.rewritten or query
        return self._inner.search(search_q, top_k=top_k)
```


---

## 三十四、rewrite_demo 全文

```python
"""
查询改写演示 — 对比关闭 / 开启规则改写

运行：PYTHONPATH=src python3 src/day33/rewrite_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day33.constants import REWRITE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever


def _preview(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rewrite_config(RewriteConfig(enabled=enabled))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if not isinstance(retriever, RewritingRetriever):
        raise RuntimeError("expected RewritingRetriever")
    retriever.search(query, top_k=1)
    rw = retriever.last_rewrite
    if not rw:
        return "—"
    label = "rewrite" if enabled else "passthrough"
    return f"[{label}] {rw.rewritten!r} (rule={rw.rule_id or '—'})"


def main() -> int:
    print("=" * 60)
    print("  Day 33 Query Rewrite 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rewrite_config()
    print(f"\n  默认 rewrite: enabled={cfg.enabled} mode={cfg.mode}")

    for item in REWRITE_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭改写 → {_preview(store, q, enabled=False)}")
        print(f"    开启改写 → {_preview(store, q, enabled=True)}")

    print("\n  ✅ Query Rewrite 演示完成")
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

`rag_rewrite_enabled`、`rag_rewrite_pool`、`rag_rewrite_latency_ms`、`rag_hit_at_1`。

---

## 三十九、生产替换 mock

保持 `Rewriteer` 接口，注入 `HuggingFaceCrossEncoderRewriteer`，配置 `model` 字段扩展。

---

## 四十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 33 · Rewrite · ZL-NA-REQ-033 · rewriteer 精读完**

---

## 四十一、完整 rewrite_config 二次嵌入

```python
"""
查询改写配置 — 开关、模式与回退策略

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"


@dataclass
class RewriteConfig:
    """检索前查询改写策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_to_original: bool = True
    max_rewrite_len: int = 200

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        if self.max_rewrite_len < 10:
            raise ValueError("max_rewrite_len 须 >= 10")
        if self.max_rewrite_len > 500:
            raise ValueError("max_rewrite_len 须 <= 500")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_to_original": self.fallback_to_original,
            "max_rewrite_len": self.max_rewrite_len,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RewriteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_to_original=bool(data.get("fallback_to_original", True)),
            max_rewrite_len=int(data.get("max_rewrite_len", 200)),
        )
```


---

## 四十二、课堂白板：rewrite 手算表

| 步骤 | query=投资有风险 | text=投资有风险，入市需谨慎 |
|------|------------------|------------------------------|
| 子串 | 是 | → 1.0 |
| 无需后续 | — | 直接返回 |

| 步骤 | query=年化收益 | text=市场波动有风险，投资需谨慎 |
|------|--------------|--------------------------------|
| 子串 | 否 | |
| coverage | 部分 token | 低 |
| bigram | 少 | 低 |
| 结论 | rewrite 低于含「年化收益率可达 8%」的 chunk |

---

## 四十三、Incident 剧本

1. 监控 口语命中 骤降  
2. PUT enabled=false  
3. 对比 hybrid-only 恢复  
4. 查 pool 是否过小或 mock 伤害业务  
5. 回滚版本或调 pool  

---

## 四十四、与 frontend 联动

`frontend/knowledge.js` status 栏展示 `rewrite` / `recall-only` — 运营一眼知改写状态。

---

## 四十五、50 项自检（续 21–30）

21. 能解释 Decorator 模式  
22. 能解释 invalidate_cache  
23. 能解释 STORE_VERSION 与 platform_version 区别  
24. 能解释 test_max_rewrite_len_respected  
25. 能解释 test_invalid_rewrite_model_422  
26. 能写 curl 关 rewrite  
27. 能对比 口语命中 与 top-3  
28. 能解释 ANN 不可用于 cross  
29. 能解释 TF-IDF 与 rewrite 无关  
30. 能完整复述三阶段漏斗
