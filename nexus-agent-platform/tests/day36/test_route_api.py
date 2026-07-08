"""Day 36 Route API 测试。"""

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


def test_get_route_config_default(client):
    data = client.get("/api/knowledge/route-config").json()
    assert data["enabled"] is True
    assert data["fallback_intent"] == "rag_standard"


def test_put_route_config(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "rag_wide",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fallback_intent"] == "rag_wide"


def test_route_preview_faq_fast(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "faq_fast"
    assert data["expand"] is False


def test_citation_preview_with_route(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("route")
    assert data["route"]["intent"] == "rag_wide"


def test_status_includes_route_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.37.0"
    assert status["route_config"]["enabled"] is True


def test_chat_includes_route(client):
    resp = client.post("/api/chat", json={"message": "客服电话多少？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("route")
    assert body["route"]["intent"] == "faq_fast"


def test_invalid_route_fallback_422(client):
    resp = client.put(
        "/api/knowledge/route-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_intent": "invalid",
        },
    )
    assert resp.status_code == 422


def test_route_preview_wide(client):
    resp = client.post(
        "/api/knowledge/route-preview",
        json={"query": "会不会亏"},
    )
    assert resp.status_code == 200
    assert resp.json()["expand"] is True
