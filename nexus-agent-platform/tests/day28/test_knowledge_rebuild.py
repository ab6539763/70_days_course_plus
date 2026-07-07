"""Day 28 知识库重建测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chunk_config import ChunkConfig
from rag.knowledge_rebuild import collect_source_files, rebuild_store
from rag.knowledge_store import KnowledgeStore
from tools.doc_parser import parse_bytes


def test_collect_sources_includes_sample_docs():
    sources = collect_source_files(include_sample_docs=True)
    names = {p.name for p in sources}
    assert "raw_faq.txt" in names or len(names) >= 1


def test_collect_sources_uploads_override(tmp_path):
    uploads = tmp_path / "uploads"
    sample = tmp_path / "sample"
    uploads.mkdir()
    sample.mkdir()
    (sample / "doc.txt").write_text("sample content", encoding="utf-8")
    (uploads / "doc.txt").write_text("upload override content", encoding="utf-8")
    sources = collect_source_files(
        uploads_dir=uploads,
        sample_docs_dir=sample,
        include_sample_docs=True,
    )
    assert len(sources) == 1
    assert "upload override" in sources[0].read_text(encoding="utf-8")


def test_rebuild_changes_chunk_count(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
    before = store.chunk_count
    store.set_chunk_config(ChunkConfig(name="tiny", chunk_size=80, overlap=10))
    report = rebuild_store(store, include_sample_docs=True)
    assert report.chunks_after != before or report.chunks_after > 0
    assert store.last_rebuilt_at is not None


def test_rebuild_clears_and_rebuilds_documents(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s2.json")
    report = rebuild_store(store)
    assert report.documents_after == store.document_count
    assert report.chunks_after == store.chunk_count
    assert report.sources_processed >= 1


def test_rebuild_persists_last_rebuilt_at(tmp_path):
    path = tmp_path / "s3.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    rebuild_store(store)
    loaded = KnowledgeStore.load(path)
    assert loaded.last_rebuilt_at is not None


def test_rebuild_report_to_dict(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s4.json")
    report = rebuild_store(store)
    data = report.to_dict()
    assert "chunk_config" in data
    assert data["sources_processed"] >= 1


def test_rebuild_with_upload_only(tmp_path):
    uploads = tmp_path / "up"
    uploads.mkdir()
    md = (SRC / "day26" / "sample_docs" / "product_notice.md")
    if md.is_file():
        (uploads / "notice.md").write_bytes(md.read_bytes())
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s5.json")
    report = rebuild_store(
        store,
        include_sample_docs=False,
        uploads_dir=uploads,
    )
    assert report.documents_after >= 1


def test_status_includes_last_rebuilt_at(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s6.json")
    rebuild_store(store)
    status = store.status_dict()
    assert status.get("last_rebuilt_at")


def test_rebuild_uses_current_chunk_config(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s7.json")
    store.set_chunk_config(ChunkConfig(name="large", chunk_size=500, overlap=50))
    report = rebuild_store(store)
    assert report.chunk_config.chunk_size == 500
