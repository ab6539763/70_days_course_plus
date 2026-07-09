"""Day 34 引用溯源单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chunker import TextChunk
from rag.citation_builder import Citation, build_citation_bundle, build_citations
from rag.citation_config import CitationConfig
from rag.knowledge_store import KnowledgeStore
from rag.retriever import RetrievalResult


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_citation_config_validate():
    CitationConfig().validate()
    with pytest.raises(ValueError):
        CitationConfig(max_citations=0).validate()
    with pytest.raises(ValueError):
        CitationConfig(preview_max_chars=10).validate()


def test_build_citations_from_results():
    chunk = TextChunk(
        chunk_id="c1",
        text="本产品年化收益率可达 8%",
        source="notice.txt",
        index=0,
        start_char=0,
        end_char=10,
    )
    results = [RetrievalResult(chunk=chunk, score=0.9, matched_tokens=("年化",))]
    cites = build_citations(results, preview_max_chars=50, max_items=1)
    assert len(cites) == 1
    assert cites[0].source == "notice.txt"
    assert cites[0].rank == 1


def test_citation_preview_truncates_preview():
    long_text = "x" * 200
    chunk = TextChunk(
        chunk_id="c2",
        text=long_text,
        source="s.txt",
        index=0,
        start_char=0,
        end_char=200,
    )
    results = [RetrievalResult(chunk=chunk, score=0.5)]
    cites = build_citations(results, preview_max_chars=30, max_items=1)
    assert len(cites[0].preview) <= 30


def test_fetch_citations_returns_structure(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("年化收益率")
    assert "citations" in data
    assert isinstance(data["citations"], list)


def test_fetch_citations_with_hits(tmp_path):
    store = _store(tmp_path)
    data = store.fetch_citations("投资有风险")
    assert data["citations"]
    assert data["citations"][0]["source"]


def test_fetch_citations_disabled(tmp_path):
    store = _store(tmp_path)
    store.set_citation_config(CitationConfig(enabled=False))
    data = store.fetch_citations("年化收益率")
    assert data["citations"] == []


def test_retrieve_citation_bundle_rewrite_meta(tmp_path):
    store = _store(tmp_path)
    rag = store.as_rag_service()
    bundle = rag.retrieve_citation_bundle("那个理财能赚多少")
    assert bundle.citations
    if bundle.rewrite:
        assert bundle.rewrite.changed


def test_knowledge_store_persists_citation_config(tmp_path):
    path = tmp_path / "persist.json"
    store = _store(tmp_path)
    store.store_path = path
    store.set_citation_config(CitationConfig(enabled=False, max_citations=2))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_citation_config()
    assert cfg.enabled is False
    assert cfg.max_citations == 2


def test_status_includes_citation_config(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["citation_config"]["enabled"] is True


def test_citation_to_dict():
    c = Citation(
        rank=1,
        chunk_id="a",
        source="s",
        score=0.8,
        preview="p",
        matched_tokens=("x",),
    )
    d = c.to_dict()
    assert d["rank"] == 1
    assert d["matched_tokens"] == ["x"]


def test_build_citation_bundle_empty():
    bundle = build_citation_bundle("q", [], config=CitationConfig())
    assert bundle.citations == []
