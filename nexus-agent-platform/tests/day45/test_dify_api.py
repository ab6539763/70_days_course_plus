"""Day 45 Dify API 测试。"""

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


def test_get_dify_config_default(client):
    data = client.get("/api/agent/dify-config").json()
    assert data["enabled"] is True
    assert data["workflow_name"] == "nexus-agent-workflow"


def test_put_dify_config(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["max_nodes"] == 5


def test_dify_export(client):
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 200
    data = resp.json()
    nodes = data["workflow"]["graph"]["nodes"]
    assert any(n["data"]["type"] == "start" for n in nodes)
    assert any(n["data"]["type"] == "end" for n in nodes)
    assert any(n["data"]["type"] == "tool" for n in nodes)


def test_dify_preview_rag(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert len(data["dify_trace"]) == 4


def test_dify_preview_with_history(client):
    resp = client.post(
        "/api/agent/dify-preview",
        json={
            "query": "年化收益",
            "history": ["理财产品风险大吗"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_status_includes_dify_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["dify_config"]["enabled"] is True


def test_chat_dify_mode_trace(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace")
    assert body["kind"] == "dify"


def test_chat_dify_mode_off_unchanged(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("dify_trace") is None
    assert body["kind"] == "faq"


def test_invalid_dify_max_nodes_422(client):
    resp = client.put(
        "/api/agent/dify-config",
        json={
            "enabled": True,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 999,
        },
    )
    assert resp.status_code == 422


def test_dify_export_disabled_400(client):
    client.put(
        "/api/agent/dify-config",
        json={
            "enabled": False,
            "workflow_name": "nexus-agent-workflow",
            "include_start_end": True,
            "mock_routing": True,
            "use_session_history": True,
            "return_dify_trace": True,
            "max_nodes": 10,
        },
    )
    resp = client.post("/api/agent/dify-export", json={})
    assert resp.status_code == 400
