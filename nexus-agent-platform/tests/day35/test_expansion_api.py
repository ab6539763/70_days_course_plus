"""Day 35 Expansion API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.37.0"


def test_get_expansion_config_default(client):
    data = client.get("/api/knowledge/expansion-config").json()
    assert data["enabled"] is True
    assert data["mode"] == "templates"
    assert data["max_queries"] == 4


def test_put_expansion_config(client):
    resp = client.put(
        "/api/knowledge/expansion-config",
        json={
            "enabled": True,
            "mode": "hyde_mock",
            "max_queries": 3,
            "include_original": True,
            "per_query_top_k": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "hyde_mock"


def test_expansion_preview(client):
    resp = client.post(
        "/api/knowledge/expansion-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["queries"]) >= 2
    assert data["changed"] is True


def test_citation_preview_with_expansion(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("expansion")
    assert len(data["expansion"]["queries"]) >= 2


def test_status_includes_expansion_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.37.0"
    assert status["expansion_config"]["enabled"] is True


def test_chat_includes_expansion(client):
    resp = client.post("/api/chat", json={"message": "理财安全吗？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert body.get("expansion")
    assert len(body["expansion"]["queries"]) >= 2


def test_invalid_expansion_max_queries_422(client):
    resp = client.put(
        "/api/knowledge/expansion-config",
        json={
            "enabled": True,
            "mode": "templates",
            "max_queries": 0,
            "include_original": True,
            "per_query_top_k": 5,
        },
    )
    assert resp.status_code == 422


def test_expansion_preview_hyde_mode(client):
    client.put(
        "/api/knowledge/expansion-config",
        json={
            "enabled": True,
            "mode": "hyde_mock",
            "max_queries": 4,
            "include_original": True,
            "per_query_top_k": 5,
        },
    )
    resp = client.post(
        "/api/knowledge/expansion-preview",
        json={"query": "收益怎么样"},
    )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "hyde_mock"
