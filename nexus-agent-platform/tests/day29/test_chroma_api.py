"""Day 29 Chroma API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.31.0"


def test_status_includes_chroma_fields(client):
    data = client.get("/api/knowledge/status").json()
    assert data["platform_version"] == "0.31.0"
    assert data["vector_backend"] == "chroma"
    assert data["chroma_count"] == data["chunk_count"]
    assert data["chroma_path"]


def test_rebuild_keeps_chroma_in_sync(client):
    before = client.get("/api/knowledge/status").json()["chroma_count"]
    resp = client.post("/api/knowledge/rebuild", json={"include_sample_docs": True})
    assert resp.status_code == 200
    after = client.get("/api/knowledge/status").json()
    assert after["chroma_count"] == after["chunk_count"]
    assert after["chroma_count"] == resp.json()["chunks_after"]


def test_chat_after_chroma_index(client):
    resp = client.post("/api/chat", json={"message": "产品收益怎么样？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert body["session_id"]


def test_upload_updates_chroma_count(client, tmp_path):
    md = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not md.is_file():
        pytest.skip("sample md missing")
    with md.open("rb") as fh:
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    assert resp.status_code == 200
    status = client.get("/api/knowledge/status").json()
    assert status["chroma_count"] == status["chunk_count"]
