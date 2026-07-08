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
from rag.expanding_retriever import ExpandingRetriever
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
    if isinstance(retriever, ExpandingRetriever):
        retriever = retriever.inner
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
