"""Day 35 多查询扩展单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chunker import TextChunk
from rag.expansion_config import ExpansionConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.knowledge_store import KnowledgeStore
from rag.query_expander import HyDEMockExpander, TemplateQueryExpander, build_expander
from rag.result_merger import merge_retrieval_results
from rag.retriever import KeywordRetriever, RetrievalResult


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_expansion_config_validate():
    ExpansionConfig().validate()
    with pytest.raises(ValueError):
        ExpansionConfig(max_queries=0).validate()
    with pytest.raises(ValueError):
        ExpansionConfig(mode="invalid").validate()


def test_template_expander_yields_multiple():
    cfg = ExpansionConfig(enabled=True, max_queries=4)
    exp = TemplateQueryExpander(config=cfg).expand("理财安全吗")
    assert len(exp.queries) >= 2
    assert exp.changed is True
    assert exp.rule_id == "safety_risk"


def test_hyde_expander_includes_hypothetical():
    cfg = ExpansionConfig(mode="hyde_mock", max_queries=4)
    exp = HyDEMockExpander(config=cfg).expand("年化收益")
    assert len(exp.queries) >= 2
    assert any("产品说明书" in q for q in exp.queries)


def test_merge_dedupes_chunk_id():
    chunk = TextChunk(
        chunk_id="c1",
        text="投资风险",
        source="a.txt",
        index=0,
        start_char=0,
        end_char=4,
    )
    r1 = RetrievalResult(chunk=chunk, score=0.5)
    r2 = RetrievalResult(chunk=chunk, score=0.9)
    merged = merge_retrieval_results([[r1], [r2]], top_k=3)
    assert len(merged) == 1
    assert merged[0].score == 0.9


def test_expanding_retriever_disabled():
    chunks = [
        TextChunk(
            chunk_id="c1",
            text="投资有风险",
            source="n.txt",
            index=0,
            start_char=0,
            end_char=5,
        )
    ]
    inner = KeywordRetriever(chunks)
    retriever = ExpandingRetriever(
        inner,
        config=ExpansionConfig(enabled=False),
    )
    hits = retriever.search("投资有风险", top_k=1)
    assert hits
    assert retriever.last_expansion is not None
    assert retriever.last_expansion.changed is False


def test_expanding_retriever_merges_paths():
    store = KnowledgeStore.bootstrap_from_sample_docs()
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    assert isinstance(retriever, RoutingRetriever)
    expanding = retriever.inner
    assert isinstance(expanding, ExpandingRetriever)
    hits = retriever.search("理财安全吗", top_k=3)
    assert hits
    assert expanding.last_expansion
    assert len(expanding.last_expansion.queries) >= 2


def test_fetch_citations_includes_expansion(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("理财安全吗")
    assert "expansion" in data
    assert data["expansion"]
    assert len(data["expansion"]["queries"]) >= 2


def test_knowledge_store_persists_expansion_config(tmp_path):
    store = _store(tmp_path)
    store.set_expansion_config(
        ExpansionConfig(enabled=True, max_queries=3, per_query_top_k=4)
    )
    store.save()
    loaded = KnowledgeStore.load(tmp_path / "store.json")
    cfg = loaded.get_expansion_config()
    assert cfg.max_queries == 3
    assert cfg.per_query_top_k == 4


def test_status_includes_expansion_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["platform_version"] == "0.37.0"
    assert status["expansion_config"]["enabled"] is True


def test_expansion_result_to_dict():
    exp = TemplateQueryExpander().expand("理财安全吗")
    data = exp.to_dict()
    assert data["original"] == "理财安全吗"
    assert isinstance(data["queries"], list)


def test_build_expander_mode():
    tpl = build_expander(ExpansionConfig(mode="templates"))
    hyde = build_expander(ExpansionConfig(mode="hyde_mock"))
    assert tpl.expand("test").mode == "templates"
    assert hyde.expand("test").mode == "hyde_mock"
