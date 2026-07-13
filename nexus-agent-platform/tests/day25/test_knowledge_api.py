"""Day 25 知识库 API 测试。"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from day25.constants import SAMPLE_UPLOAD_NAME, SAMPLE_UPLOAD_TEXT
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "store.json")
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version_025(client):
    data = client.get("/api/health").json()
    assert data["version"] == "0.44.0"


def test_knowledge_status(client):
    resp = client.get("/api/knowledge/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk_count"] > 0
    assert data["document_count"] >= 1
    assert data["platform_version"] == "0.44.0"


def test_knowledge_upload_txt(client):
    files = {
        "file": (SAMPLE_UPLOAD_NAME, io.BytesIO(SAMPLE_UPLOAD_TEXT.encode("utf-8")), "text/plain"),
    }
    resp = client.post("/api/knowledge/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == SAMPLE_UPLOAD_NAME
    assert data["chunk_count"] > 0
    assert data["total_chunks"] > data["chunk_count"] or data["total_chunks"] >= data["chunk_count"]


def test_knowledge_upload_rejects_unsupported(client):
    files = {"file": ("bad.docx", io.BytesIO(b"PK"), "application/octet-stream")}
    resp = client.post("/api/knowledge/upload", files=files)
    assert resp.status_code == 422


def test_knowledge_upload_empty(client):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    resp = client.post("/api/knowledge/upload", files=files)
    assert resp.status_code == 422


def test_chat_after_upload_uses_kb(client):
    files = {
        "file": (SAMPLE_UPLOAD_NAME, io.BytesIO(SAMPLE_UPLOAD_TEXT.encode("utf-8")), "text/plain"),
    }
    client.post("/api/knowledge/upload", files=files)
    resp = client.post(
        "/api/chat",
        json={"message": "最低起购金额是多少", "session_id": "kb-test"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["reply"]) > 0


def test_upload_clears_sessions(client):
    client.post("/api/chat", json={"message": "你好", "session_id": "to-clear"})
    files = {
        "file": (SAMPLE_UPLOAD_NAME, io.BytesIO(SAMPLE_UPLOAD_TEXT.encode("utf-8")), "text/plain"),
    }
    upload = client.post("/api/knowledge/upload", files=files)
    assert upload.json()["sessions_cleared"] >= 1


def test_frontend_knowledge_js(client):
    text = client.get("/knowledge.js").text
    assert "NexusKnowledge" in text
    assert "uploadFile" in text
