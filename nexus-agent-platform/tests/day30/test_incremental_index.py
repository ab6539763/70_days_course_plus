"""Day 30 增量索引测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_rebuild import rebuild_store
from rag.knowledge_store import INDEX_MODE_FULL, INDEX_MODE_INCREMENTAL, KnowledgeStore


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _sample_md_bytes() -> bytes:
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    return sample.read_bytes()


def test_reupload_does_not_reset_chroma(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)

    with patch.object(ChromaVectorIndex, "reset") as mock_reset:
        store.ingest_bytes(data, filename="notice.md", incremental=True)
        assert mock_reset.call_count == 0

    assert store._chroma_index().count() == store.chunk_count
    assert store.index_mode == INDEX_MODE_INCREMENTAL


def test_reupload_replaces_document_not_duplicates(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    docs_after_first = store.document_count
    chunks_after_first = store.chunk_count

    store.ingest_bytes(data, filename="notice.md", incremental=True)
    assert store.document_count == docs_after_first
    assert store.chunk_count == chunks_after_first
    names = [d.name for d in store.documents]
    assert names.count("notice.md") == 1


def test_incremental_updates_last_incremental_at(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    assert store.last_incremental_at is not None


def test_chroma_count_matches_chunks_after_incremental(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    status = store.status_dict()
    assert status["chroma_count"] == status["chunk_count"]


def test_remove_document_by_source_deletes_chroma_vectors(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma_before = store._chroma_index().count()
    removed = store._remove_document_by_source("notice.md")
    assert removed
    assert store._chroma_index().count() < chroma_before
    assert not any(c.source == "notice.md" for c in store.chunks)


def test_rebuild_still_uses_full_index_mode(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rebuild_store(store)
    assert store.index_mode == INDEX_MODE_FULL


def test_incremental_persists_index_mode(tmp_path):
    path = tmp_path / "persist.json"
    store = _store(tmp_path)
    store.store_path = path
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    store.save(path)
    loaded = KnowledgeStore.load(path)
    loaded.chroma_path = tmp_path / "chroma"
    assert loaded.index_mode == INDEX_MODE_INCREMENTAL
    assert loaded.last_incremental_at


def test_non_incremental_ingest_uses_full_rebuild(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    from tools.doc_parser import parse_bytes

    parsed = parse_bytes(data, "notice.md")
    store.ingest_parsed(parsed, incremental=False)
    assert store.index_mode == INDEX_MODE_FULL


def test_chroma_delete_by_source(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma = store._chroma_index()
    deleted = chroma.delete_by_source("notice.md")
    assert deleted >= 1
    assert chroma.count() == store.chunk_count - deleted or chroma.count() == 0


def test_rag_retrieval_after_incremental_upload(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rag = store.as_rag_service()
    ctx = rag.retrieve_context("年化收益")
    assert ctx and "未检索" not in ctx
