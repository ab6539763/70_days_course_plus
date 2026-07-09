"""Day 25 知识库存储与 ingestion 测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.paths import get_path
from day25.constants import SAMPLE_UPLOAD_TEXT
from rag.embedding import TfidfEmbeddingModel
from rag.ingestion import ingest_upload
from rag.knowledge_store import KnowledgeStore, get_knowledge_store, set_knowledge_store


@pytest.fixture
def tmp_store(tmp_path):
    store_path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=store_path)
    set_knowledge_store(store)
    yield store
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())


def test_bootstrap_has_chunks(tmp_store):
    assert tmp_store.document_count >= 1
    assert tmp_store.chunk_count >= 3


def test_ingest_text_appends_chunks(tmp_store):
    before = tmp_store.chunk_count
    meta = tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="extra.txt")
    assert meta.chunk_count > 0
    assert tmp_store.chunk_count == before + meta.chunk_count


def test_rag_retrieve_after_ingest(tmp_store):
    tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="faq_extra.txt")
    ctx = tmp_store.as_rag_service().retrieve_context("最低起购金额")
    assert "1000" in ctx or "起购" in ctx


def test_save_and_load_roundtrip(tmp_store, tmp_path):
    path = tmp_path / "roundtrip.json"
    tmp_store.ingest_text("测试持久化文本内容。", filename="persist.txt")
    tmp_store.save(path)

    loaded = KnowledgeStore.load(path)
    assert loaded.chunk_count == tmp_store.chunk_count
    assert loaded.document_count == tmp_store.document_count
    ctx = loaded.as_rag_service().retrieve_context("持久化")
    assert "持久化" in ctx


def test_embedding_export_load_state():
    model = TfidfEmbeddingModel()
    model.fit(["年化收益", "风险提示", "起购金额"])
    state = model.export_state()
    restored = TfidfEmbeddingModel()
    restored.load_state(state)
    assert restored.is_fitted
    assert restored.dimension == model.dimension


def test_status_dict(tmp_store):
    data = tmp_store.status_dict()
    assert data["chunk_count"] == tmp_store.chunk_count
    assert data["platform_version"] == "0.43.0"
    assert isinstance(data["documents"], list)


def test_get_knowledge_store_singleton(tmp_store):
    a = get_knowledge_store()
    b = get_knowledge_store()
    assert a is b


def test_ingest_upload_writes_file(tmp_store, tmp_path, monkeypatch):
    monkeypatch.setitem(
        __import__("core.paths", fromlist=["PATHS"]).PATHS,
        "knowledge_uploads",
        tmp_path / "uploads",
    )
    data = SAMPLE_UPLOAD_TEXT.encode("utf-8")
    meta = ingest_upload(data, "uploaded.txt", store=tmp_store, uploads_dir=tmp_path / "uploads")
    assert meta.name == "uploaded.txt"
    assert (tmp_path / "uploads" / "uploaded.txt").is_file()


def test_ingest_empty_raises(tmp_store):
    with pytest.raises(ValueError):
        tmp_store.ingest_text("   ", filename="empty.txt")


def test_store_json_has_version(tmp_store, tmp_path):
    path = tmp_path / "v.json"
    tmp_store.save(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == "1.1"
    assert raw["platform_version"] == "0.43.0"
