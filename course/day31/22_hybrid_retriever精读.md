# Day 31 精读：hybrid_retriever 与融合层

**需求**：ZL-NA-REQ-031 | **学时**：120 min

---

## 一、hybrid_retriever.py 全文

```python
"""
混合检索器 — 关键词 + 向量分数融合

将 KeywordRetriever（稀疏命中）与 ChromaEmbeddingRetriever（稠密相似度）
按加权或 RRF 合并，改善精确词与语义问句的召回平衡。

需求：ZL-NA-REQ-031
"""

from __future__ import annotations

from rag.chunker import TextChunk
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.retrieval_config import (
    FUSION_RRF,
    FUSION_WEIGHTED,
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)
from rag.retriever import KeywordRetriever, RetrievalResult


class HybridRetriever:
    """
    混合检索器 — 统一 search() 接口

    典型用法：
        cfg = RetrievalConfig(mode="hybrid", fusion="rrf")
        retriever = HybridRetriever(chunks, keyword, vector, config=cfg)
        hits = retriever.search("最低起购金额", top_k=3)
    """

    def __init__(
        self,
        chunks: list[TextChunk],
        keyword: KeywordRetriever,
        vector: ChromaEmbeddingRetriever | EmbeddingRetriever,
        *,
        config: RetrievalConfig | None = None,
    ) -> None:
        self._chunks = list(chunks)
        self._keyword = keyword
        self._vector = vector
        self._config = config or RetrievalConfig()

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks:
            return []

        cfg = self._config
        if cfg.mode == MODE_VECTOR:
            return self._vector.search(query, top_k=top_k)
        if cfg.mode == MODE_KEYWORD:
            return self._keyword.search(query, top_k=top_k)

        pool = max(top_k * 4, 8)
        kw_hits = self._keyword.search(query, top_k=pool)
        vec_hits = self._vector.search(query, top_k=pool)
        if cfg.fusion == FUSION_RRF:
            merged = _rrf_merge(kw_hits, vec_hits, rrf_k=cfg.rrf_k)
        else:
            merged = _weighted_merge(
                kw_hits,
                vec_hits,
                keyword_weight=cfg.keyword_weight,
                vector_weight=cfg.vector_weight,
            )
        return merged[: max(1, top_k)]


def _weighted_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    keyword_weight: float,
    vector_weight: float,
) -> list[RetrievalResult]:
    """按归一化分数加权求和"""
    kw_norm = _normalize_scores(kw_hits)
    vec_norm = _normalize_scores(vec_hits)
    by_id: dict[str, RetrievalResult] = {}

    for r in kw_hits:
        by_id[r.chunk.chunk_id] = r
    for r in vec_hits:
        by_id.setdefault(r.chunk.chunk_id, r)

    scored: list[RetrievalResult] = []
    for chunk_id, base in by_id.items():
        ks = kw_norm.get(chunk_id, 0.0)
        vs = vec_norm.get(chunk_id, 0.0)
        combined = keyword_weight * ks + vector_weight * vs
        if combined <= 0:
            continue
        matched = tuple(dict.fromkeys((*base.matched_tokens,)))
        scored.append(
            RetrievalResult(
                chunk=base.chunk,
                score=combined,
                matched_tokens=matched,
            )
        )
    scored.sort(key=lambda r: (-r.score, r.chunk.index))
    return scored


def _rrf_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    rrf_k: int,
) -> list[RetrievalResult]:
    """Reciprocal Rank Fusion — 不依赖原始分数尺度"""
    scores: dict[str, float] = {}
    chunks: dict[str, TextChunk] = {}
    tokens: dict[str, tuple[str, ...]] = {}

    for rank, r in enumerate(kw_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        tokens[cid] = r.matched_tokens

    for rank, r in enumerate(vec_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        if r.matched_tokens:
            prev = tokens.get(cid, ())
            tokens[cid] = tuple(dict.fromkeys((*prev, *r.matched_tokens)))

    max_rrf = max(scores.values()) if scores else 1.0
    results = [
        RetrievalResult(
            chunk=chunks[cid],
            score=scores[cid] / max_rrf,
            matched_tokens=tokens.get(cid, ()),
        )
        for cid in scores
    ]
    results.sort(key=lambda r: (-r.score, r.chunk.index))
    return results


def _normalize_scores(hits: list[RetrievalResult]) -> dict[str, float]:
    if not hits:
        return {}
    max_s = max(r.score for r in hits) or 1.0
    return {r.chunk.chunk_id: r.score / max_s for r in hits}
```


---

## 二、行级注释：模块头与导入（L1–L23）

| 行 | 代码 | 讲解 |
|----|------|------|
| L1–L8 | 模块 docstring | 声明 ZL-NA-REQ-031；点明 keyword+vector 融合目标 |
| L12–L13 | TextChunk / Chroma | 向量腿走 Chroma；chunk 元数据贯穿 RetrievalResult |
| L15–L22 | retrieval_config 常量 | 避免魔法字符串；与 API JSON 枚举一致 |
| L23 | KeywordRetriever | 稀疏腿；token 重叠 + TF 分数 |

---

## 三、行级注释：HybridRetriever 类（L26–L55）

| 行 | 讲解 |
|----|------|
| L36–L47 | 构造器注入双检索器 + 可选 config；默认 `RetrievalConfig()` |
| L49–L51 | `chunk_count` 代理 chunks 长度，供 status 展示 |
| L53–L55 | `config` 只读属性，测试中断言 fusion 切换 |

---

## 四、行级注释：search 主流程（L57–L80）

```python
def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks:
            return []

        cfg = self._config
        if cfg.mode == MODE_VECTOR:
            return self._vector.search(query, top_k=top_k)
        if cfg.mode == MODE_KEYWORD:
            return self._keyword.search(query, top_k=top_k)

        pool = max(top_k * 4, 8)
        kw_hits = self._keyword.search(query, top_k=pool)
        vec_hits = self._vector.search(query, top_k=pool)
        if cfg.fusion == FUSION_RRF:
            merged = _rrf_merge(kw_hits, vec_hits, rrf_k=cfg.rrf_k)
        else:
            merged = _weighted_merge(
                kw_hits,
                vec_hits,
                keyword_weight=cfg.keyword_weight,
                vector_weight=cfg.vector_weight,
            )
        return merged[: max(1, top_k)]
```


| 行 | 讲解 |
|----|------|
| L58–L60 | 空 query / 空库 → 早返回 `[]`，防无意义 Chroma 调用 |
| L63–L66 | **单模式早返回**：性能与语义清晰，不做假融合 |
| L68 | `pool = max(top_k * 4, 8)` 候选池 — **必读考点** |
| L69–L70 | 同 query、同 pool 各搜一路 |
| L71–L79 | fusion 二分；`merged[:max(1, top_k)]` 保证至少尝试返回 1 条（有结果时） |

---

## 五、_weighted_merge 全文与注释

```python
def _weighted_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    keyword_weight: float,
    vector_weight: float,
) -> list[RetrievalResult]:
    """按归一化分数加权求和"""
    kw_norm = _normalize_scores(kw_hits)
    vec_norm = _normalize_scores(vec_hits)
    by_id: dict[str, RetrievalResult] = {}

    for r in kw_hits:
        by_id[r.chunk.chunk_id] = r
    for r in vec_hits:
        by_id.setdefault(r.chunk.chunk_id, r)

    scored: list[RetrievalResult] = []
    for chunk_id, base in by_id.items():
        ks = kw_norm.get(chunk_id, 0.0)
        vs = vec_norm.get(chunk_id, 0.0)
        combined = keyword_weight * ks + vector_weight * vs
        if combined <= 0:
            continue
        matched = tuple(dict.fromkeys((*base.matched_tokens,)))
        scored.append(
            RetrievalResult(
                chunk=base.chunk,
                score=combined,
                matched_tokens=matched,
            )
        )
    scored.sort(key=lambda r: (-r.score, r.chunk.index))
    return scored
```


| 行 | 讲解 |
|----|------|
| L91–L92 | 分路 max 归一化 → [0,1]，消除 TF 与 cosine 量纲差 |
| L95–L98 | 并集 chunk_id；keyword 优先写入，vector `setdefault` 补新 id |
| L102–L104 | 加权求和；`combined<=0` 跳过两路都未有效打分的 id |
| L107 | matched_tokens 去重保序 |
| L115 | 次键 `chunk.index` 稳定排序 |

---

## 六、_rrf_merge 全文与注释

```python
def _rrf_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    rrf_k: int,
) -> list[RetrievalResult]:
    """Reciprocal Rank Fusion — 不依赖原始分数尺度"""
    scores: dict[str, float] = {}
    chunks: dict[str, TextChunk] = {}
    tokens: dict[str, tuple[str, ...]] = {}

    for rank, r in enumerate(kw_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        tokens[cid] = r.matched_tokens

    for rank, r in enumerate(vec_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        if r.matched_tokens:
            prev = tokens.get(cid, ())
            tokens[cid] = tuple(dict.fromkeys((*prev, *r.matched_tokens)))

    max_rrf = max(scores.values()) if scores else 1.0
    results = [
        RetrievalResult(
            chunk=chunks[cid],
            score=scores[cid] / max_rrf,
            matched_tokens=tokens.get(cid, ()),
        )
        for cid in scores
    ]
    results.sort(key=lambda r: (-r.score, r.chunk.index))
    return results
```


| 行 | 讲解 |
|----|------|
| L130–L134 | keyword 路：按 rank 累加 `1/(rrf_k+rank)`，记 tokens |
| L136–L142 | vector 路：同公式累加；合并 matched_tokens |
| L144–L152 | 除以 `max_rrf` 归一化展示分；排序规则同 weighted |

**考点**：同一 chunk 两路都靠前 → RRF 分叠加 → hybrid 优势场景。

---

## 七、_normalize_scores

```python
def _normalize_scores(hits: list[RetrievalResult]) -> dict[str, float]:
    if not hits:
        return {}
    max_s = max(r.score for r in hits) or 1.0
    return {r.chunk.chunk_id: r.score / max_s for r in hits}
```

空列表返回 `{}` — 作业 E 考点。`or 1.0` 防全零除零。

---

## 八、retrieval_config.py 全文

```python
"""
检索配置 — 关键词 / 向量 / 混合模式与融合参数

需求：ZL-NA-REQ-031
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MODE_VECTOR = "vector"
MODE_KEYWORD = "keyword"
MODE_HYBRID = "hybrid"
FUSION_WEIGHTED = "weighted"
FUSION_RRF = "rrf"


@dataclass
class RetrievalConfig:
    """知识库检索策略配置"""

    mode: str = MODE_HYBRID
    keyword_weight: float = 0.35
    vector_weight: float = 0.65
    fusion: str = FUSION_WEIGHTED
    rrf_k: int = 60

    def validate(self) -> None:
        if self.mode not in (MODE_VECTOR, MODE_KEYWORD, MODE_HYBRID):
            raise ValueError(f"mode 须为 vector|keyword|hybrid，收到 {self.mode!r}")
        if self.fusion not in (FUSION_WEIGHTED, FUSION_RRF):
            raise ValueError(f"fusion 须为 weighted|rrf，收到 {self.fusion!r}")
        if self.mode == MODE_HYBRID:
            total = self.keyword_weight + self.vector_weight
            if total <= 0:
                raise ValueError("混合模式下 keyword_weight + vector_weight 须 > 0")
        if self.rrf_k < 1:
            raise ValueError("rrf_k 须 >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "keyword_weight": round(self.keyword_weight, 4),
            "vector_weight": round(self.vector_weight, 4),
            "fusion": self.fusion,
            "rrf_k": self.rrf_k,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RetrievalConfig:
        if not data:
            return cls()
        return cls(
            mode=str(data.get("mode", MODE_HYBRID)),
            keyword_weight=float(data.get("keyword_weight", 0.35)),
            vector_weight=float(data.get("vector_weight", 0.65)),
            fusion=str(data.get("fusion", FUSION_WEIGHTED)),
            rrf_k=int(data.get("rrf_k", 60)),
        )
```


`validate()` 在 hybrid 模式只要求权重和 >0，**不要**求和为 1 — 允许运营放大整体尺度。

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
        expanding = ExpandingRetriever(rewriting, config=expansion_cfg)
        route_cfg = self.get_route_config()
        retriever = RoutingRetriever(expanding, config=route_cfg)
        index = DocumentIndex(chunks=self.chunks, retriever=retriever)
        return RAGContextService(index)
```


HybridRetriever 成为 `DocumentIndex` 唯一 retriever；chat 无感知融合细节。

---

## 十、测试精读 test_hybrid_retriever.py

```python
"""Day 31 混合检索单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.chroma_store import ChromaVectorIndex
from rag.embedding import EmbeddingClient
from rag.hybrid_retriever import HybridRetriever, _rrf_merge, _weighted_merge
from rag.expanding_retriever import ExpandingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.rewriting_retriever import RewritingRetriever
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import (
    FUSION_RRF,
    FUSION_WEIGHTED,
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)
from rag.retriever import KeywordRetriever, RetrievalResult


def _hybrid_store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _build_hybrid(store: KnowledgeStore) -> HybridRetriever:
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if isinstance(retriever, RoutingRetriever):
        retriever = retriever.inner
    if isinstance(retriever, ExpandingRetriever):
        retriever = retriever.inner
    if isinstance(retriever, RewritingRetriever):
        retriever = retriever.inner
    if isinstance(retriever, RerankingRetriever):
        assert isinstance(retriever.inner, HybridRetriever)
        return retriever.inner
    assert isinstance(retriever, HybridRetriever)
    return retriever


def test_retrieval_config_validate():
    cfg = RetrievalConfig(mode="hybrid", keyword_weight=0.5, vector_weight=0.5)
    cfg.validate()
    with pytest.raises(ValueError):
        RetrievalConfig(mode="invalid").validate()


def test_hybrid_mode_vector_only(tmp_path):
    store = _hybrid_store(tmp_path)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_VECTOR))
    h = _build_hybrid(store)
    hits = h.search("年化收益", top_k=2)
    assert len(hits) >= 1


def test_hybrid_mode_keyword_only(tmp_path):
    store = _hybrid_store(tmp_path)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_KEYWORD))
    h = _build_hybrid(store)
    hits = h.search("年化收益率", top_k=2)
    assert len(hits) >= 1


def test_hybrid_weighted_merge(tmp_path):
    store = _hybrid_store(tmp_path)
    store.set_retrieval_config(
        RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_WEIGHTED, keyword_weight=0.5, vector_weight=0.5)
    )
    h = _build_hybrid(store)
    hits = h.search("投资有风险", top_k=3)
    assert hits
    assert hits[0].score > 0


def test_hybrid_rrf_merge(tmp_path):
    store = _hybrid_store(tmp_path)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF, rrf_k=60))
    h = _build_hybrid(store)
    hits = h.search("投资有风险吗", top_k=3)
    assert len(hits) >= 1


def test_exact_phone_keyword_favors_hybrid(tmp_path):
    store = _hybrid_store(tmp_path)
    query = "13900001111"
    vec = _build_hybrid(store)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_VECTOR))
    vec_hits = vec.search(query, top_k=1)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_KEYWORD))
    kw_hits = vec.search(query, top_k=1)
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID))
    hy_hits = vec.search(query, top_k=1)
    assert kw_hits or hy_hits
    if kw_hits:
        assert "13900001111" in kw_hits[0].chunk.text or hy_hits


def test_knowledge_store_persists_retrieval_config(tmp_path):
    path = tmp_path / "persist.json"
    store = _hybrid_store(tmp_path)
    store.store_path = path
    store.set_retrieval_config(RetrievalConfig(mode=MODE_KEYWORD, fusion=FUSION_RRF))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    assert loaded.get_retrieval_config().mode == MODE_KEYWORD
    assert loaded.get_retrieval_config().fusion == FUSION_RRF


def test_status_includes_retrieval_config(tmp_path):
    store = _hybrid_store(tmp_path)
    status = store.status_dict()
    assert status["retrieval_config"]["mode"] == MODE_HYBRID


def test_rrf_merge_helper():
    from rag.chunker import TextChunk

    c1 = TextChunk(chunk_id="a", text="t1", source="s", index=0, start_char=0, end_char=2)
    c2 = TextChunk(chunk_id="b", text="t2", source="s", index=1, start_char=0, end_char=2)
    kw = [RetrievalResult(chunk=c1, score=0.9, matched_tokens=("x",))]
    vec = [RetrievalResult(chunk=c2, score=0.8, matched_tokens=())]
    merged = _rrf_merge(kw, vec, rrf_k=60)
    assert len(merged) == 2


def test_weighted_merge_helper():
    from rag.chunker import TextChunk

    c = TextChunk(chunk_id="a", text="same", source="s", index=0, start_char=0, end_char=4)
    r = RetrievalResult(chunk=c, score=1.0, matched_tokens=("q",))
    merged = _weighted_merge([r], [r], keyword_weight=0.5, vector_weight=0.5)
    assert len(merged) == 1
    assert merged[0].score > 0
```


| 测试 | 要点 |
|------|------|
| test_retrieval_config_validate | 非法 mode 抛错 |
| test_hybrid_mode_vector_only | 早返回向量腿 |
| test_hybrid_weighted_merge | score>0 |
| test_hybrid_rrf_merge | RRF 路径 smoke |
| test_exact_phone_keyword_favors_hybrid | **业务金测** |
| test_rrf_merge_helper | 纯函数 2 条合并 |
| test_weighted_merge_helper | 同 id 双路 |

---

## 十一、API 测试 test_hybrid_api.py

```python
"""Day 31 混合检索 API 测试。"""

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


def test_get_retrieval_config_default_hybrid(client):
    data = client.get("/api/knowledge/retrieval-config").json()
    assert data["mode"] == "hybrid"
    assert data["fusion"] in ("weighted", "rrf")


def test_put_retrieval_config_rrf(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={
            "mode": "hybrid",
            "fusion": "rrf",
            "keyword_weight": 0.4,
            "vector_weight": 0.6,
            "rrf_k": 60,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fusion"] == "rrf"


def test_status_includes_retrieval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["retrieval_config"]["mode"] == "hybrid"


def test_invalid_retrieval_mode_422(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "invalid", "fusion": "weighted"},
    )
    assert resp.status_code == 422


def test_chat_with_hybrid_retrieval(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_switch_to_keyword_mode(client):
    client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "keyword", "fusion": "weighted", "keyword_weight": 1.0, "vector_weight": 0.0},
    )
    cfg = client.get("/api/knowledge/retrieval-config").json()
    assert cfg["mode"] == "keyword"
```


`test_health_version` 锁版本 `v0.31.0`；`test_chat_with_hybrid_retrieval` 端到端。

---

## 十二、调试清单

- [ ] 打印 kw_hits / vec_hits 各前 5  
- [ ] 打印 fusion 后前 3 score  
- [ ] 切换 mode 对比是否早返回  
- [ ] 查 store.json retrieval_config  

---

## 十三、自检

1. 手绘 hybrid search 流程图。  
2. 口述 RRF 对 rank=1 的贡献。  
3. 说明为何 weighted 必须 normalize。

---

## 十四、笔试模拟

**1（20分）** 证明：当 keyword 路与 vector 路 top-1 不同 id 时，RRF 可能使「两路都排前5」的 id 胜出。

**2（20分）** 解释 `pool` 过小导致融合失效的反例。

**3（20分）** 对比 FR-002 与 FR-003 的实现位置。

---

## 十五、与 Day30 衔接

增量更新 chunk 后，HybridRetriever 持有新 chunks 引用；**无需**为混合检索单独 rebuild。若 TF-IDF 扩张 reset，两路索引同时更新。

---

## 十六、完整 knowledge_store 交叉引用（节选）

```python
def get_retrieval_config(self) -> RetrievalConfig:
        return RetrievalConfig.from_dict(self.retrieval_config.to_dict())

    def set_retrieval_config(self, config: RetrievalConfig) -> RetrievalConfig:
        config.validate()
        self.retrieval_config = RetrievalConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.retrieval_config

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

    def get_expansion_config(self) -> ExpansionConfig:
        return ExpansionConfig.from_dict(self.expansion_config.to_dict())

    def set_expansion_config(self, config: ExpansionConfig) -> ExpansionConfig:
        config.validate()
        self.expansion_config = ExpansionConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.expansion_config

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


`set_retrieval_config` 深拷贝 `from_dict(to_dict())` 防别名突变。

---

## 十七、口语考试题

1. 30 秒解释 hybrid 是什么。  
2. 1 分钟对比 weighted vs RRF。  
3. 白板画 search 分支。

---

## 十八、实验记录模板

| query | mode | fusion | top1_id | top1_score |
|-------|------|--------|---------|------------|
| | | | | |

---

## 十九、FAQ

**Q 能否 async 并行两路？** 可优化；当前同步教学实现。  
**Q matched_tokens 空？** vector 腿常为空，正常。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `HybridRetriever.search` 与两种 merge 函数，并映射到 ZL-NA-REQ-031 的 FR-001–FR-003。

---

## 二十一、hybrid_retriever 完整源码（重复嵌入便于打印）

```python
"""
混合检索器 — 关键词 + 向量分数融合

将 KeywordRetriever（稀疏命中）与 ChromaEmbeddingRetriever（稠密相似度）
按加权或 RRF 合并，改善精确词与语义问句的召回平衡。

需求：ZL-NA-REQ-031
"""

from __future__ import annotations

from rag.chunker import TextChunk
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.retrieval_config import (
    FUSION_RRF,
    FUSION_WEIGHTED,
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)
from rag.retriever import KeywordRetriever, RetrievalResult


class HybridRetriever:
    """
    混合检索器 — 统一 search() 接口

    典型用法：
        cfg = RetrievalConfig(mode="hybrid", fusion="rrf")
        retriever = HybridRetriever(chunks, keyword, vector, config=cfg)
        hits = retriever.search("最低起购金额", top_k=3)
    """

    def __init__(
        self,
        chunks: list[TextChunk],
        keyword: KeywordRetriever,
        vector: ChromaEmbeddingRetriever | EmbeddingRetriever,
        *,
        config: RetrievalConfig | None = None,
    ) -> None:
        self._chunks = list(chunks)
        self._keyword = keyword
        self._vector = vector
        self._config = config or RetrievalConfig()

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks:
            return []

        cfg = self._config
        if cfg.mode == MODE_VECTOR:
            return self._vector.search(query, top_k=top_k)
        if cfg.mode == MODE_KEYWORD:
            return self._keyword.search(query, top_k=top_k)

        pool = max(top_k * 4, 8)
        kw_hits = self._keyword.search(query, top_k=pool)
        vec_hits = self._vector.search(query, top_k=pool)
        if cfg.fusion == FUSION_RRF:
            merged = _rrf_merge(kw_hits, vec_hits, rrf_k=cfg.rrf_k)
        else:
            merged = _weighted_merge(
                kw_hits,
                vec_hits,
                keyword_weight=cfg.keyword_weight,
                vector_weight=cfg.vector_weight,
            )
        return merged[: max(1, top_k)]


def _weighted_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    keyword_weight: float,
    vector_weight: float,
) -> list[RetrievalResult]:
    """按归一化分数加权求和"""
    kw_norm = _normalize_scores(kw_hits)
    vec_norm = _normalize_scores(vec_hits)
    by_id: dict[str, RetrievalResult] = {}

    for r in kw_hits:
        by_id[r.chunk.chunk_id] = r
    for r in vec_hits:
        by_id.setdefault(r.chunk.chunk_id, r)

    scored: list[RetrievalResult] = []
    for chunk_id, base in by_id.items():
        ks = kw_norm.get(chunk_id, 0.0)
        vs = vec_norm.get(chunk_id, 0.0)
        combined = keyword_weight * ks + vector_weight * vs
        if combined <= 0:
            continue
        matched = tuple(dict.fromkeys((*base.matched_tokens,)))
        scored.append(
            RetrievalResult(
                chunk=base.chunk,
                score=combined,
                matched_tokens=matched,
            )
        )
    scored.sort(key=lambda r: (-r.score, r.chunk.index))
    return scored


def _rrf_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    rrf_k: int,
) -> list[RetrievalResult]:
    """Reciprocal Rank Fusion — 不依赖原始分数尺度"""
    scores: dict[str, float] = {}
    chunks: dict[str, TextChunk] = {}
    tokens: dict[str, tuple[str, ...]] = {}

    for rank, r in enumerate(kw_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        tokens[cid] = r.matched_tokens

    for rank, r in enumerate(vec_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        if r.matched_tokens:
            prev = tokens.get(cid, ())
            tokens[cid] = tuple(dict.fromkeys((*prev, *r.matched_tokens)))

    max_rrf = max(scores.values()) if scores else 1.0
    results = [
        RetrievalResult(
            chunk=chunks[cid],
            score=scores[cid] / max_rrf,
            matched_tokens=tokens.get(cid, ()),
        )
        for cid in scores
    ]
    results.sort(key=lambda r: (-r.score, r.chunk.index))
    return results


def _normalize_scores(hits: list[RetrievalResult]) -> dict[str, float]:
    if not hits:
        return {}
    max_s = max(r.score for r in hits) or 1.0
    return {r.chunk.chunk_id: r.score / max_s for r in hits}
```


---

## 二十二、融合函数对照伪代码

```
function HYBRID_SEARCH(q, top_k):
    if mode == vector: return VEC(q, top_k)
    if mode == keyword: return KW(q, top_k)
    P = max(top_k * 4, 8)
    a = KW(q, P)
    b = VEC(q, P)
    if fusion == rrf: return RRF(a, b)[:top_k]
    return WEIGHTED(a, b)[:top_k]
```

---

## 二十三、HYBRID_QUERIES 业务解读

| query | 业务意图 | keyword 腿 | vector 腿 |
|-------|----------|------------|-----------|
| 年化收益率可达 | 产品收益 FAQ | 命中「年化」「8%」 | 语义近邻 |
| 13900001111 | 查电话 | **强命中号码** | 易漂移到风险段 |
| 投资有风险 | 合规披露 | 「风险」token | 语义概括 |

---

## 二十四、测试与 FR 映射（完整）

| 测试 | FR/NFR |
|------|--------|
| test_retrieval_config_validate | FR-004 |
| test_hybrid_mode_vector_only | FR-002 |
| test_hybrid_mode_keyword_only | FR-002 |
| test_hybrid_weighted_merge | FR-003 |
| test_hybrid_rrf_merge | FR-003 |
| test_exact_phone_keyword_favors_hybrid | AC-03 |
| test_knowledge_store_persists_retrieval_config | FR-005 |
| test_status_includes_retrieval_config | FR-005 |
| test_rrf_merge_helper | FR-003 |
| test_weighted_merge_helper | FR-003 |
| test_health_version | FR-008 |
| test_get_retrieval_config_default_hybrid | AC-01 |
| test_put_retrieval_config_rrf | AC-02 |
| test_invalid_retrieval_mode_422 | FR-006 |
| test_chat_with_hybrid_retrieval | AC-05 |
| test_switch_to_keyword_mode | FR-002 |

---

## 二十五、knowledge API 全文（检索相关上下文）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-035 / ZL-NA-REQ-036 / ZL-NA-REQ-037 / ZL-NA-REQ-038
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


@router.post("/citation-preview", response_model=CitationPreviewResponse)
def citation_preview(body: CitationPreviewRequest) -> CitationPreviewResponse:
    """预览单条 query 的检索引用（含 rewrite / expansion 审计）"""
    store = get_knowledge_store()
    data = store.fetch_citations(body.query)
    return CitationPreviewResponse(**data)


@router.get("/expansion-config", response_model=ExpansionConfigResponse)
def get_expansion_config() -> ExpansionConfigResponse:
    """返回多 query 扩展开关与参数"""
    cfg = get_knowledge_store().get_expansion_config()
    return ExpansionConfigResponse(**cfg.to_dict())


@router.put("/expansion-config", response_model=ExpansionConfigResponse)
def update_expansion_config(body: ExpansionConfigRequest) -> ExpansionConfigResponse:
    """更新多 query 扩展策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = ExpansionConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_expansion_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExpansionConfigResponse(**cfg.to_dict())


@router.post("/expansion-preview", response_model=ExpansionPreviewResponse)
def expansion_preview(body: ExpansionPreviewRequest) -> ExpansionPreviewResponse:
    """预览单条 query 的多路扩展结果"""
    store = get_knowledge_store()
    cfg = store.get_expansion_config()
    expander = build_expander(cfg)
    result = expander.expand(body.query)
    return ExpansionPreviewResponse(**result.to_dict())


@router.get("/route-config", response_model=RouteConfigResponse)
def get_route_config() -> RouteConfigResponse:
    """返回检索管线路由开关与默认意图"""
    cfg = get_knowledge_store().get_route_config()
    return RouteConfigResponse(**cfg.to_dict())


@router.put("/route-config", response_model=RouteConfigResponse)
def update_route_config(body: RouteConfigRequest) -> RouteConfigResponse:
    """更新检索管线路由策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = RouteConfig.from_dict(bod
```


---

## 二十六、phase3_hybrid_review 建议

课后运行 `src/day31/phase3_hybrid_review.py`（若存在）串联 Day25–31 概念。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| RRF 用原始分 | 用 rank |
| hybrid 一定优于 vector | 取决于 query 与权重 |
| PUT 不 save | API 内 save |

---

## 二十八、50 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 RRF 公式  
3. 能解释 normalize  
4. 能定位 _build_rag_service  
5. 能 curl GET retrieval-config  
6. 能 curl PUT rrf  
7. 能跑 hybrid_demo  
8. 能跑 hybrid_api_demo  
9. 能数清 17 tests  
10. 能解释 13900001111 案例  
11. 能对比 Day30 正交  
12. 能预告 Day32 rerank  
13. 能读 validate 源码  
14. 能读 setdefault 语义  
15. 能解释 matched_tokens  
16. 能解释 chunk.index tie-break  
17. 能解释 MODE_* 常量  
18. 能解释 FUSION_* 常量  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-031 目标  

---

## 二十九、延伸阅读：Retriever 接口

KeywordRetriever 与 ChromaEmbeddingRetriever 均实现 `search(query, top_k)` → `list[RetrievalResult]`。HybridRetriever 是 **Decorator / Facade** 模式，统一对外接口。

---

## 三十、完整测试文件（API）

```python
"""Day 31 混合检索 API 测试。"""

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


def test_get_retrieval_config_default_hybrid(client):
    data = client.get("/api/knowledge/retrieval-config").json()
    assert data["mode"] == "hybrid"
    assert data["fusion"] in ("weighted", "rrf")


def test_put_retrieval_config_rrf(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={
            "mode": "hybrid",
            "fusion": "rrf",
            "keyword_weight": 0.4,
            "vector_weight": 0.6,
            "rrf_k": 60,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fusion"] == "rrf"


def test_status_includes_retrieval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["retrieval_config"]["mode"] == "hybrid"


def test_invalid_retrieval_mode_422(client):
    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "invalid", "fusion": "weighted"},
    )
    assert resp.status_code == 422


def test_chat_with_hybrid_retrieval(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_switch_to_keyword_mode(client):
    client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "keyword", "fusion": "weighted", "keyword_weight": 1.0, "vector_weight": 0.0},
    )
    cfg = client.get("/api/knowledge/retrieval-config").json()
    assert cfg["mode"] == "keyword"
```


---

## 三十一、课堂录音稿（8 min）

「打开 hybrid_retriever，找到 search。先看两个 if：vector、keyword 单腿。然后 pool。记住四倍与八。fusion 分支：weighted 先 normalize 再加权；rrf 只看排名。最后截断 top_k。这就是 ZL-NA-REQ-031 的全部读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): hybrid retrieval with RRF/weighted fusion (ZL-NA-REQ-031)

- HybridRetriever + RetrievalConfig
- GET/PUT /api/knowledge/retrieval-config
- tests/day31 (17 cases)
```

---

## 三十三、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 31 · 混合检索 · ZL-NA-REQ-031 · hybrid_retriever 精读完**
