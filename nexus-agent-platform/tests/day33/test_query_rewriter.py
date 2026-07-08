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
