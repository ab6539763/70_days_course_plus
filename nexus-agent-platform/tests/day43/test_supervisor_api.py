"""Day 43 Supervisor API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_supervisor_config_default(client):
    data = client.get("/api/agent/supervisor-config").json()
    assert data["enabled"] is True
    assert data["max_delegations"] == 1


def test_put_supervisor_config(client):
    resp = client.put(
        "/api/agent/supervisor-config",
        json={
            "enabled": True,
            "max_delegations": 2,
            "use_session_history": True,
            "return_delegation_trace": True,
            "mock_routing": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_delegations"] == 2


def test_supervisor_preview_rag(client):
    resp = client.post(
        "/api/agent/supervisor-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_worker" in data["delegated_agents"]
    assert "rag_search" in data["tools_used"]


def test_supervisor_preview_with_history(client):
    resp = client.post(
        "/api/agent/supervisor-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_supervisor_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["supervisor_config"]["enabled"] is True


def test_chat_supervisor_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "supervisor_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("supervisor_trace")
    assert body.get("delegated_agents")
    assert body["kind"] == "supervisor"


def test_chat_supervisor_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("supervisor_trace") is None
    assert body["kind"] == "faq"


def test_invalid_supervisor_max_delegations_422(client):
    resp = client.put(
        "/api/agent/supervisor-config",
        json={
            "enabled": True,
            "max_delegations": 99,
            "use_session_history": True,
            "return_delegation_trace": True,
            "mock_routing": True,
        },
    )
    assert resp.status_code == 422
