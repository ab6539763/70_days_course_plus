"""Day 28 重建 API 测试。"""

from __future__ import annotations

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
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "store.json")
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version_028(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_rebuild_endpoint(client):
    resp = client.post(
        "/api/knowledge/rebuild",
        json={"include_sample_docs": True, "apply_best_config": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunks_after"] > 0
    assert data["sources_processed"] >= 1
    assert data["sessions_cleared"] >= 0
    assert "rebuilt_at" in data


def test_rebuild_with_best_config(client):
    resp = client.post(
        "/api/knowledge/rebuild",
        json={"include_sample_docs": True, "apply_best_config": True},
    )
    assert resp.status_code == 200
    assert resp.json()["documents_after"] >= 1


def test_status_after_rebuild(client):
    client.post("/api/knowledge/rebuild", json={})
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status.get("last_rebuilt_at")


def test_chat_after_rebuild(client):
    client.post("/api/knowledge/rebuild", json={})
    chat = client.post(
        "/api/chat",
        json={"message": "投资有风险吗", "session_id": "post-rebuild"},
    )
    assert chat.status_code == 200
