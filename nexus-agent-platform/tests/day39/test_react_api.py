"""Day 39 ReAct API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.44.0"


def test_get_react_config_default(client):
    data = client.get("/api/agent/react-config").json()
    assert data["enabled"] is True
    assert data["max_steps"] == 3


def test_put_react_config(client):
    resp = client.put(
        "/api/agent/react-config",
        json={
            "enabled": True,
            "max_steps": 4,
            "use_session_history": True,
            "mock_planner": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_steps"] == 4


def test_react_preview_faq(client):
    resp = client.post(
        "/api/agent/react-preview",
        json={"query": "客服热线是多少"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "faq_lookup" in data["tools_used"]
    assert len(data["steps"]) >= 2


def test_react_preview_with_history(client):
    resp = client.post(
        "/api/agent/react-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_react_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.44.0"
    assert status["react_config"]["enabled"] is True


def test_chat_agent_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "agent_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("agent_trace")
    assert body.get("tools_used")
    assert body["kind"] == "agent"


def test_chat_agent_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("agent_trace") is None
    assert body["kind"] == "faq"


def test_invalid_react_max_steps_422(client):
    resp = client.put(
        "/api/agent/react-config",
        json={
            "enabled": True,
            "max_steps": 99,
            "use_session_history": True,
            "mock_planner": True,
        },
    )
    assert resp.status_code == 422
