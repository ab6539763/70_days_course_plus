"""Day 36 查询路由单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.expanding_retriever import ExpandingRetriever
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
    assert isinstance(exp, ExpandingRetriever)
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
    assert isinstance(retriever.inner, ExpandingRetriever)
