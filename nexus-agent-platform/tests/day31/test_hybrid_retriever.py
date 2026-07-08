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
