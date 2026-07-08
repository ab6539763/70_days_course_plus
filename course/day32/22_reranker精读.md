# Day 32 精读：reranker 与两阶段检索管线

**需求**：ZL-NA-REQ-032 | **学时**：120 min

---

## 一、reranker.py 全文

```python
"""
交叉编码器重排 — 对 hybrid 召回候选逐对精排

MockCrossEncoder 用 query-chunk 双向 token 覆盖 + 子串命中模拟
交叉编码器行为，无需加载 HuggingFace 模型。

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from rag.retriever import RetrievalResult, _tokenize

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+")


class Reranker(ABC):
    """重排器抽象接口"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """对候选列表按 query-chunk 相关性重排并截断"""


class MockCrossEncoderReranker(Reranker):
    """
    教学用 Mock 交叉编码器

    与 bi-encoder（向量检索）不同，逐对计算 query 与 chunk 的细粒度交互：
    - 完整子串命中加权
    - token 覆盖率
    - 连续 bigram 共现奖励
    - 过长 chunk 轻微惩罚（降低噪声段落排名）
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not candidates:
            return []

        scored: list[RetrievalResult] = []
        for item in candidates:
            score = score_pair(query, item.chunk.text)
            if score <= 0:
                continue
            scored.append(
                RetrievalResult(
                    chunk=item.chunk,
                    score=score,
                    matched_tokens=item.matched_tokens,
                )
            )

        scored.sort(key=lambda r: (-r.score, r.chunk.index))
        return scored[: max(1, top_k)]


def score_pair(query: str, text: str) -> float:
    """模拟 cross-encoder 对 (query, chunk) 的相关性打分"""
    q = query.strip().lower()
    t = text.lower()
    if not q or not t:
        return 0.0

    if q in t:
        return 1.0

    tokens = _tokenize(q)
    if not tokens:
        return 0.0

    matched = [tok for tok in tokens if tok in t]
    coverage = len(matched) / len(tokens)

    bigram_bonus = _bigram_overlap(q, t)
    length_penalty = min(len(t) / 2500.0, 0.12)

    raw = coverage * 0.65 + bigram_bonus * 0.35 - length_penalty
    return max(0.0, min(1.0, raw))


def _bigram_overlap(query: str, text: str) -> float:
    """查询连续二字/词在文本中共现的比例"""
    units: list[str] = []
    for part in _TOKEN_PATTERN.findall(query):
        units.append(part.lower())
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                units.append(part[i : i + 2].lower())

    if not units:
        return 0.0

    hits = sum(1 for u in units if u in text)
    return hits / len(units)
```


---

## 二、行级注释：Reranker 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rerank(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、MockCrossEncoderReranker（L33–L68）

```python
class MockCrossEncoderReranker(Reranker):
    """
    教学用 Mock 交叉编码器

    与 bi-encoder（向量检索）不同，逐对计算 query 与 chunk 的细粒度交互：
    - 完整子串命中加权
    - token 覆盖率
    - 连续 bigram 共现奖励
    - 过长 chunk 轻微惩罚（降低噪声段落排名）
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not candidates:
            return []

        scored: list[RetrievalResult] = []
        for item in candidates:
            score = score_pair(query, item.chunk.text)
            if score <= 0:
                continue
            scored.append(
                RetrievalResult(
                    chunk=item.chunk,
                    score=score,
                    matched_tokens=item.matched_tokens,
                )
            )

        scored.sort(key=lambda r: (-r.score, r.chunk.index))
        return scored[: max(1, top_k)]
```


| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `score_pair`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、score_pair 全文

```python
def score_pair(query: str, text: str) -> float:
    """模拟 cross-encoder 对 (query, chunk) 的相关性打分"""
    q = query.strip().lower()
    t = text.lower()
    if not q or not t:
        return 0.0

    if q in t:
        return 1.0

    tokens = _tokenize(q)
    if not tokens:
        return 0.0

    matched = [tok for tok in tokens if tok in t]
    coverage = len(matched) / len(tokens)

    bigram_bonus = _bigram_overlap(q, t)
    length_penalty = min(len(t) / 2500.0, 0.12)

    raw = coverage * 0.65 + bigram_bonus * 0.35 - length_penalty
    return max(0.0, min(1.0, raw))
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
def _bigram_overlap(query: str, text: str) -> float:
    """查询连续二字/词在文本中共现的比例"""
    units: list[str] = []
    for part in _TOKEN_PATTERN.findall(query):
        units.append(part.lower())
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                units.append(part[i : i + 2].lower())

    if not units:
        return 0.0

    hits = sum(1 for u in units if u in text)
    return hits / len(units)
```


中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、reranking_retriever.py 全文

```python
"""
Reranking 检索管线 — hybrid 宽召回 → cross-encoder 精排

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker, Reranker
from rag.retriever import RetrievalResult


class RerankingRetriever:
    """
    两阶段检索器 — 内层负责召回，外层 reranker 负责精排

    典型用法：
        inner = HybridRetriever(...)
        retriever = RerankingRetriever(inner, config=RerankConfig())
        hits = retriever.search("年化收益率", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        reranker: Reranker | None = None,
        config: RerankConfig | None = None,
    ) -> None:
        self._inner = inner
        self._reranker = reranker or MockCrossEncoderReranker()
        self._config = config or RerankConfig()

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RerankConfig:
        return self._config

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            return []

        cfg = self._config
        if not cfg.enabled:
            return self._inner.search(query, top_k=top_k)

        pool = max(cfg.candidate_pool, top_k)
        candidates = self._inner.search(query, top_k=pool)
        if not candidates:
            return []

        return self._reranker.rerank(query, candidates, top_k=top_k)
```


---

## 七、search 主流程

```python
def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            return []

        cfg = self._config
        if not cfg.enabled:
            return self._inner.search(query, top_k=top_k)

        pool = max(cfg.candidate_pool, top_k)
        candidates = self._inner.search(query, top_k=pool)
        if not candidates:
            return []
```


| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rerank 开销 |
| pool 计算 | `max(candidate_pool, top_k)` |
| candidates | inner hybrid 宽召回 |
| rerank 调用 | MockCrossEncoder 精排截断 |

---

## 八、rerank_config.py 全文

```python
"""
Rerank 配置 — 候选池大小、开关与模型标识

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODEL_MOCK = "mock"


@dataclass
class RerankConfig:
    """混合召回后的交叉编码器重排策略"""

    enabled: bool = True
    candidate_pool: int = 20
    model: str = MODEL_MOCK

    def validate(self) -> None:
        if self.candidate_pool < 1:
            raise ValueError("candidate_pool 须 >= 1")
        if self.candidate_pool > 100:
            raise ValueError("candidate_pool 须 <= 100")
        if self.model not in (MODEL_MOCK,):
            raise ValueError(f"model 须为 mock，收到 {self.model!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "candidate_pool": self.candidate_pool,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RerankConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            candidate_pool=int(data.get("candidate_pool", 20)),
            model=str(data.get("model", MODEL_MOCK)),
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


`RerankingRetriever(hybrid, ...)` — chat 无感知精排细节。

---

## 十、测试精读 test_reranker.py

```python
"""Day 32 Rerank 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chunker import TextChunk
from rag.hybrid_retriever import HybridRetriever
from rag.knowledge_store import KnowledgeStore
from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker, score_pair
from rag.reranking_retriever import RerankingRetriever
from rag.rewriting_retriever import RewritingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult


def _rerank_store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _get_reranking(store: KnowledgeStore) -> RerankingRetriever:
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if isinstance(retriever, RewritingRetriever):
        retriever = retriever.inner
    assert isinstance(retriever, RerankingRetriever)
    return retriever


def test_rerank_config_validate():
    RerankConfig(enabled=True, candidate_pool=20).validate()
    with pytest.raises(ValueError):
        RerankConfig(candidate_pool=0).validate()
    with pytest.raises(ValueError):
        RerankConfig(model="bert").validate()


def test_score_pair_exact_substring():
    assert score_pair("投资有风险", "投资有风险，入市需谨慎") >= 0.9


def test_score_pair_partial_coverage():
    s = score_pair("年化收益率", "本产品年化收益率可达 8%")
    assert s > 0.5


def test_mock_rerank_reorders_candidates():
    c_noise = TextChunk(
        chunk_id="n",
        text="员工不得将内部资料传播至公司外部，违反者将按纪律处分。",
        source="policy.txt",
        index=0,
        start_char=0,
        end_char=20,
    )
    c_target = TextChunk(
        chunk_id="t",
        text="本产品年化收益率可达 8%，请仔细阅读风险揭示书。",
        source="notice.txt",
        index=1,
        start_char=0,
        end_char=20,
    )
    candidates = [
        RetrievalResult(chunk=c_noise, score=0.95, matched_tokens=()),
        RetrievalResult(chunk=c_target, score=0.40, matched_tokens=("年化",)),
    ]
    reranked = MockCrossEncoderReranker().rerank("年化收益率可达", candidates, top_k=1)
    assert reranked[0].chunk.chunk_id == "t"


def test_reranking_retriever_disabled_delegates(tmp_path):
    store = _rerank_store(tmp_path)
    store.set_rerank_config(RerankConfig(enabled=False))
    r = _get_reranking(store)
    hits = r.search("投资有风险", top_k=2)
    assert hits


def test_reranking_retriever_enabled(tmp_path):
    store = _rerank_store(tmp_path)
    store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=20))
    r = _get_reranking(store)
    hits = r.search("年化收益率", top_k=3)
    assert len(hits) >= 1
    assert hits[0].score > 0


def test_phone_query_rerank(tmp_path):
    store = _rerank_store(tmp_path)
    store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=20))
    r = _get_reranking(store)
    hits = r.search("13900001111", top_k=1)
    assert hits
    assert "13900001111" in hits[0].chunk.text


def test_knowledge_store_persists_rerank_config(tmp_path):
    path = tmp_path / "persist.json"
    store = _rerank_store(tmp_path)
    store.store_path = path
    store.set_rerank_config(RerankConfig(enabled=False, candidate_pool=15))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_rerank_config()
    assert cfg.enabled is False
    assert cfg.candidate_pool == 15


def test_status_includes_rerank_config(tmp_path):
    store = _rerank_store(tmp_path)
    status = store.status_dict()
    assert status["rerank_config"]["enabled"] is True
    assert status["rerank_config"]["candidate_pool"] == 20


def test_inner_hybrid_accessible(tmp_path):
    store = _rerank_store(tmp_path)
    r = _get_reranking(store)
    assert isinstance(r.inner, HybridRetriever)


def test_candidate_pool_respected(tmp_path):
    store = _rerank_store(tmp_path)
    store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=5))
    r = _get_reranking(store)
    hits = r.search("投资", top_k=2)
    assert len(hits) <= 2
```


| 测试 | 要点 |
|------|------|
| test_mock_rerank_reorders_candidates | **翻牌金测** |
| test_score_pair_exact_substring | 子串=1.0 |
| test_phone_query_rerank | 业务号码 |
| test_reranking_retriever_disabled | 降级路径 |
| test_inner_hybrid_accessible | inner 类型 |
| test_knowledge_store_persists_rerank_config | 持久化 |

---

## 十一、API 测试 test_rerank_api.py

```python
"""Day 32 Rerank API 测试。"""

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


def test_get_rerank_config_default(client):
    data = client.get("/api/knowledge/rerank-config").json()
    assert data["enabled"] is True
    assert data["candidate_pool"] == 20
    assert data["model"] == "mock"


def test_put_rerank_config_disable(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": False, "candidate_pool": 10, "model": "mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    assert resp.json()["candidate_pool"] == 10


def test_status_includes_rerank_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.34.0"
    assert status["rerank_config"]["enabled"] is True


def test_invalid_rerank_pool_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 0, "model": "mock"},
    )
    assert resp.status_code == 422


def test_chat_with_rerank(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_invalid_rerank_model_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 20, "model": "bert"},
    )
    assert resp.status_code == 422
```


`test_health_version` 锁版本 `v0.32.0`；`test_chat_with_rerank` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rerank 后前 3 的 score_pair  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json rerank_config  

---

## 十三、自检

1. 手绘两阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rerank 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 hit@1 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day31 衔接

HybridRetriever 仍是 inner；关 rerank 即回 Day31 行为。retrieval_config 与 rerank_config 正交。

---

## 十六、knowledge_store rerank 方法

```python
def get_rerank_config(self) -> RerankConfig:
        return RerankConfig.from_dict(self.rerank_config.to_dict())

    def set_rerank_config(self, config: RerankConfig) -> RerankConfig:
        config.validate()
        self.rerank_config = RerankConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.rerank_config

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


`set_rerank_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rerank 是什么。  
2. 1 分钟对比召回与精排。  
3. 白板画 RerankingRetriever.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q 能否 async batch score_pair？** 可优化；当前同步教学实现。  
**Q matched_tokens 会变吗？** rerank 保留原 matched_tokens，只换 score。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RerankingRetriever.search` 与 `score_pair`，并映射到 ZL-NA-REQ-032 的 FR-001–FR-003。

---

## 二十一、reranker 完整源码（重复嵌入便于打印）

```python
"""
交叉编码器重排 — 对 hybrid 召回候选逐对精排

MockCrossEncoder 用 query-chunk 双向 token 覆盖 + 子串命中模拟
交叉编码器行为，无需加载 HuggingFace 模型。

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from rag.retriever import RetrievalResult, _tokenize

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+")


class Reranker(ABC):
    """重排器抽象接口"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """对候选列表按 query-chunk 相关性重排并截断"""


class MockCrossEncoderReranker(Reranker):
    """
    教学用 Mock 交叉编码器

    与 bi-encoder（向量检索）不同，逐对计算 query 与 chunk 的细粒度交互：
    - 完整子串命中加权
    - token 覆盖率
    - 连续 bigram 共现奖励
    - 过长 chunk 轻微惩罚（降低噪声段落排名）
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not candidates:
            return []

        scored: list[RetrievalResult] = []
        for item in candidates:
            score = score_pair(query, item.chunk.text)
            if score <= 0:
                continue
            scored.append(
                RetrievalResult(
                    chunk=item.chunk,
                    score=score,
                    matched_tokens=item.matched_tokens,
                )
            )

        scored.sort(key=lambda r: (-r.score, r.chunk.index))
        return scored[: max(1, top_k)]


def score_pair(query: str, text: str) -> float:
    """模拟 cross-encoder 对 (query, chunk) 的相关性打分"""
    q = query.strip().lower()
    t = text.lower()
    if not q or not t:
        return 0.0

    if q in t:
        return 1.0

    tokens = _tokenize(q)
    if not tokens:
        return 0.0

    matched = [tok for tok in tokens if tok in t]
    coverage = len(matched) / len(tokens)

    bigram_bonus = _bigram_overlap(q, t)
    length_penalty = min(len(t) / 2500.0, 0.12)

    raw = coverage * 0.65 + bigram_bonus * 0.35 - length_penalty
    return max(0.0, min(1.0, raw))


def _bigram_overlap(query: str, text: str) -> float:
    """查询连续二字/词在文本中共现的比例"""
    units: list[str] = []
    for part in _TOKEN_PATTERN.findall(query):
        units.append(part.lower())
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                units.append(part[i : i + 2].lower())

    if not units:
        return 0.0

    hits = sum(1 for u in units if u in text)
    return hits / len(units)
```


---

## 二十二、两阶段伪代码

```
function RERANKING_SEARCH(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(candidate_pool, top_k)
    C = INNER(q, P)          # HybridRetriever
    return RERANK(q, C, top_k)
```

---

## 二十三、RERANK_QUERIES 业务解读

| query | 业务意图 | rerank 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_rerank_config_validate | FR-004 |
| test_mock_rerank_reorders_candidates | FR-002 |
| test_reranking_retriever_enabled | FR-003 |
| test_phone_query_rerank | AC-03 |
| test_knowledge_store_persists_rerank_config | FR-005 |
| test_health_version | FR-008 |
| test_put_rerank_config_disable | AC-02 |
| test_chat_with_rerank | AC-05 |

---

## 二十五、knowledge API 节选（rerank 上下文）

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

## 二十六、phase3_rerank_review 建议

课后运行 `src/day32/phase3_rerank_review.py` 串联 Day25–32。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| rerank 替代 hybrid | 外包层 |
| hybrid 分与 rerank 分可比 | 仅排序 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 score_pair 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET rerank-config  
6. 能 curl PUT 关 rerank  
7. 能跑 rerank_demo  
8. 能跑 rerank_api_demo  
9. 能数清 18 tests  
10. 能解释翻牌测试  
11. 能对比 Day31  
12. 能预告 Day33 rewrite  
13. 能读 validate 源码  
14. 能解释 inner 属性  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 candidate_pool 上限 100  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-032 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`RerankingRetriever` 是 **Decorator**：对外统一 `search`，对内委托 `HybridRetriever`。与 Day31 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 32 Rerank API 测试。"""

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


def test_get_rerank_config_default(client):
    data = client.get("/api/knowledge/rerank-config").json()
    assert data["enabled"] is True
    assert data["candidate_pool"] == 20
    assert data["model"] == "mock"


def test_put_rerank_config_disable(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": False, "candidate_pool": 10, "model": "mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    assert resp.json()["candidate_pool"] == 10


def test_status_includes_rerank_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.34.0"
    assert status["rerank_config"]["enabled"] is True


def test_invalid_rerank_pool_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 0, "model": "mock"},
    )
    assert resp.status_code == 422


def test_chat_with_rerank(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_invalid_rerank_model_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 20, "model": "bert"},
    )
    assert resp.status_code == 422
```


---

## 三十一、课堂录音稿（8 min）

「打开 reranking_retriever，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，reranker 逐对 score_pair，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rerank pipeline (ZL-NA-REQ-032)

- RerankingRetriever + RerankConfig
- GET/PUT /api/knowledge/rerank-config
- tests/day32 (18 cases)
```

---

## 三十三、reranking_retriever 二次嵌入

```python
"""
Reranking 检索管线 — hybrid 宽召回 → cross-encoder 精排

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker, Reranker
from rag.retriever import RetrievalResult


class RerankingRetriever:
    """
    两阶段检索器 — 内层负责召回，外层 reranker 负责精排

    典型用法：
        inner = HybridRetriever(...)
        retriever = RerankingRetriever(inner, config=RerankConfig())
        hits = retriever.search("年化收益率", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        reranker: Reranker | None = None,
        config: RerankConfig | None = None,
    ) -> None:
        self._inner = inner
        self._reranker = reranker or MockCrossEncoderReranker()
        self._config = config or RerankConfig()

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RerankConfig:
        return self._config

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            return []

        cfg = self._config
        if not cfg.enabled:
            return self._inner.search(query, top_k=top_k)

        pool = max(cfg.candidate_pool, top_k)
        candidates = self._inner.search(query, top_k=pool)
        if not candidates:
            return []

        return self._reranker.rerank(query, candidates, top_k=top_k)
```


---

## 三十四、rerank_demo 全文

```python
"""
Rerank 演示 — 对比关闭 / 开启精排

运行：PYTHONPATH=src python3 src/day32/rerank_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day32.constants import RERANK_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rerank_config import RerankConfig
from rag.reranking_retriever import RerankingRetriever
from rag.rewriting_retriever import RewritingRetriever


def _top_hit(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rerank_config(RerankConfig(enabled=enabled, candidate_pool=20))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if not isinstance(retriever, RewritingRetriever):
        raise RuntimeError("expected RewritingRetriever")
    if not isinstance(retriever.inner, RerankingRetriever):
        raise RuntimeError("expected RerankingRetriever inner")
    hits = retriever.search(query, top_k=1)
    if not hits:
        return "—"
    preview = hits[0].chunk.text[:40].replace("\n", " ")
    label = "rerank" if enabled else "recall"
    return f"[{label}] {hits[0].chunk.source} ({hits[0].score:.2f}) {preview}…"


def main() -> int:
    print("=" * 60)
    print("  Day 32 Rerank 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rerank_config()
    print(f"\n  默认 rerank: enabled={cfg.enabled} pool={cfg.candidate_pool}")

    for item in RERANK_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭精排 → {_top_hit(store, q, enabled=False)}")
        print(f"    开启精排 → {_top_hit(store, q, enabled=True)}")

    print("\n  ✅ Rerank 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 三十五、延迟估算习题

pool=20，单次 score_pair 0.5ms → rerank 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、hit@1 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rerank 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_rerank_enabled`、`rag_rerank_pool`、`rag_rerank_latency_ms`、`rag_hit_at_1`。

---

## 三十九、生产替换 mock

保持 `Reranker` 接口，注入 `HuggingFaceCrossEncoderReranker`，配置 `model` 字段扩展。

---

## 四十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 32 · Rerank · ZL-NA-REQ-032 · reranker 精读完**

---

## 四十一、完整 rerank_config 二次嵌入

```python
"""
Rerank 配置 — 候选池大小、开关与模型标识

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODEL_MOCK = "mock"


@dataclass
class RerankConfig:
    """混合召回后的交叉编码器重排策略"""

    enabled: bool = True
    candidate_pool: int = 20
    model: str = MODEL_MOCK

    def validate(self) -> None:
        if self.candidate_pool < 1:
            raise ValueError("candidate_pool 须 >= 1")
        if self.candidate_pool > 100:
            raise ValueError("candidate_pool 须 <= 100")
        if self.model not in (MODEL_MOCK,):
            raise ValueError(f"model 须为 mock，收到 {self.model!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "candidate_pool": self.candidate_pool,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RerankConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            candidate_pool=int(data.get("candidate_pool", 20)),
            model=str(data.get("model", MODEL_MOCK)),
        )
```


---

## 四十二、课堂白板：score_pair 手算表

| 步骤 | query=投资有风险 | text=投资有风险，入市需谨慎 |
|------|------------------|------------------------------|
| 子串 | 是 | → 1.0 |
| 无需后续 | — | 直接返回 |

| 步骤 | query=年化收益 | text=市场波动有风险，投资需谨慎 |
|------|--------------|--------------------------------|
| 子串 | 否 | |
| coverage | 部分 token | 低 |
| bigram | 少 | 低 |
| 结论 | rerank 低于含「年化收益率可达 8%」的 chunk |

---

## 四十三、Incident 剧本

1. 监控 hit@1 骤降  
2. PUT enabled=false  
3. 对比 hybrid-only 恢复  
4. 查 pool 是否过小或 mock 伤害业务  
5. 回滚版本或调 pool  

---

## 四十四、与 frontend 联动

`frontend/knowledge.js` status 栏展示 `rerank` / `recall-only` — 运营一眼知精排状态。

---

## 四十五、50 项自检（续 21–30）

21. 能解释 Decorator 模式  
22. 能解释 invalidate_cache  
23. 能解释 STORE_VERSION 与 platform_version 区别  
24. 能解释 test_candidate_pool_respected  
25. 能解释 test_invalid_rerank_model_422  
26. 能写 curl 关 rerank  
27. 能对比 hit@1 与 top-3  
28. 能解释 ANN 不可用于 cross  
29. 能解释 TF-IDF 与 rerank 无关  
30. 能完整复述两阶段漏斗
