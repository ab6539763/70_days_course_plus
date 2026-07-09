"""Day 33 Query Rewrite API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_get_rewrite_config_default(client):
    data = client.get("/api/knowledge/rewrite-config").json()
    assert data["enabled"] is True
    assert data["mode"] == "rules"


def test_put_rewrite_config_disable(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": False,
            "mode": "rules",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_rewrite_preview_colloquial(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "那个理财能赚多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["changed"] is True
    assert "年化" in data["rewritten"]


def test_status_includes_rewrite_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.39.0"
    assert status["rewrite_config"]["enabled"] is True


def test_invalid_rewrite_mode_422(client):
    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": True,
            "mode": "llm",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    assert resp.status_code == 422


def test_chat_with_rewrite(client):
    resp = client.post("/api/chat", json={"message": "那个理财能赚多少？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_rewrite_preview_unchanged(client):
    resp = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "年化收益率可达"},
    )
    assert resp.status_code == 200
    assert resp.json()["changed"] is False
