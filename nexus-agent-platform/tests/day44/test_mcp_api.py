"""Day 44 MCP API 测试。"""

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


def test_get_mcp_config_default(client):
    data = client.get("/api/agent/mcp-config").json()
    assert data["enabled"] is True
    assert data["server_name"] == "nexus-tools"


def test_put_mcp_config(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_tool_calls"] == 3


def test_mcp_list_tools(client):
    resp = client.post("/api/agent/mcp-list-tools", json={})
    assert resp.status_code == 200
    data = resp.json()
    names = {t["name"] for t in data["tools"]}
    assert "faq_lookup" in names
    assert data["server_name"] == "nexus-tools"


def test_mcp_preview_rag(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "rag_search" in data["mcp_tools"]


def test_mcp_preview_with_history(client):
    resp = client.post(
        "/api/agent/mcp-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_mcp_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["mcp_config"]["enabled"] is True


def test_chat_mcp_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace")
    assert body.get("mcp_tools")
    assert body["kind"] == "mcp"


def test_chat_mcp_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("mcp_trace") is None
    assert body["kind"] == "faq"


def test_invalid_mcp_max_tool_calls_422(client):
    resp = client.put(
        "/api/agent/mcp-config",
        json={
            "enabled": True,
            "server_name": "nexus-tools",
            "expose_external_tools": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_mcp_trace": True,
            "max_tool_calls": 99,
        },
    )
    assert resp.status_code == 422
