"""Day 32 Rerank API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.34.0"


def test_get_rerank_config_default(client):
    data = client.get("/api/knowledge/rerank-config").json()
    assert data["enabled"] is True
    assert data["candidate_pool"] == 20
    assert data["model"] == "mock"


def test_put_rerank_config_disable(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": False, "candidate_pool": 10, "model": "mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    assert resp.json()["candidate_pool"] == 10


def test_status_includes_rerank_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.34.0"
    assert status["rerank_config"]["enabled"] is True


def test_invalid_rerank_pool_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 0, "model": "mock"},
    )
    assert resp.status_code == 422


def test_chat_with_rerank(client):
    resp = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_invalid_rerank_model_422(client):
    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 20, "model": "bert"},
    )
    assert resp.status_code == 422
