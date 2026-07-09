"""Day 41 StateGraph API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.41.0"


def test_get_graph_config_default(client):
    data = client.get("/api/agent/graph-config").json()
    assert data["enabled"] is True
    assert data["max_iterations"] == 3


def test_put_graph_config(client):
    resp = client.put(
        "/api/agent/graph-config",
        json={
            "enabled": True,
            "max_iterations": 4,
            "use_session_history": True,
            "return_node_trace": True,
            "mock_planner": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_iterations"] == 4


def test_graph_preview_faq(client):
    resp = client.post(
        "/api/agent/graph-preview",
        json={"query": "客服热线是多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "faq_lookup" in data["tools_used"]
    assert "planner" in data["node_path"]


def test_graph_preview_with_history(client):
    resp = client.post(
        "/api/agent/graph-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_graph_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.41.0"
    assert status["graph_config"]["enabled"] is True


def test_chat_graph_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "graph_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("graph_trace")
    assert body.get("tools_used")
    assert body["kind"] == "graph"


def test_chat_graph_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("graph_trace") is None
    assert body["kind"] == "faq"


def test_invalid_graph_max_iterations_422(client):
    resp = client.put(
        "/api/agent/graph-config",
        json={
            "enabled": True,
            "max_iterations": 99,
            "use_session_history": True,
            "return_node_trace": True,
            "mock_planner": True,
        },
    )
    assert resp.status_code == 422
