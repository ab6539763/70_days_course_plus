"""Day 34 Citation API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.42.0"


def test_get_citation_config_default(client):
    data = client.get("/api/knowledge/citation-config").json()
    assert data["enabled"] is True
    assert data["max_citations"] == 3


def test_put_citation_config(client):
    resp = client.put(
        "/api/knowledge/citation-config",
        json={
            "enabled": True,
            "max_citations": 2,
            "preview_max_chars": 80,
            "include_rewrite_meta": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_citations"] == 2


def test_citation_preview(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "年化收益率是多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source"]


def test_citation_preview_with_rewrite(client):
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "那个理财能赚多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("rewrite")
    assert data["rewrite"]["changed"] is True


def test_status_includes_citation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.42.0"
    assert status["citation_config"]["enabled"] is True


def test_chat_includes_citations(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert isinstance(body.get("citations"), list)


def test_invalid_citation_max_422(client):
    resp = client.put(
        "/api/knowledge/citation-config",
        json={
            "enabled": True,
            "max_citations": 0,
            "preview_max_chars": 120,
            "include_rewrite_meta": True,
        },
    )
    assert resp.status_code == 422


def test_citation_preview_disabled(client):
    client.put(
        "/api/knowledge/citation-config",
        json={
            "enabled": False,
            "max_citations": 3,
            "preview_max_chars": 120,
            "include_rewrite_meta": True,
        },
    )
    resp = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "年化收益率"},
    )
    assert resp.status_code == 200
    assert resp.json()["citations"] == []
