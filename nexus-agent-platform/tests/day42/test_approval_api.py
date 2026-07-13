"""Day 42 Approval API 测试。"""

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

from agent.approval_checkpoint import approval_checkpoint_store
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


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


def test_get_approval_config_default(client):
    data = client.get("/api/agent/approval-config").json()
    assert data["enabled"] is True
    assert data["mock_auto_approve"] is True


def test_put_approval_config(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员A",
            "reject_message": "驳回",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mock_auto_approve"] is False


def test_approval_preview_rag_auto(client):
    resp = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "human_approval" in data["node_path"]
    assert data["approval_status"] == "approved"


def test_approval_interrupt_resume(client):
    client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员",
            "reject_message": "审批未通过",
        },
    )
    preview = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["interrupted"] is True
    cid = body["checkpoint_id"]
    assert cid

    resume = client.post(
        "/api/agent/approval-resume",
        json={"checkpoint_id": cid, "approved": True, "comment": "通过"},
    )
    assert resume.status_code == 200
    assert resume.json()["approval_status"] == "approved"


def test_status_includes_approval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["approval_config"]["enabled"] is True


def test_chat_approval_mode(client):
    resp = client.post(
        "/api/chat",
        json={"message": "年化收益", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert body.get("approval")
    assert body.get("graph_trace")


def test_chat_approval_mode_faq(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert "faq_lookup" in (body.get("tools_used") or [])


def test_invalid_reviewer_label_422(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": True,
            "reviewer_label": "",
            "reject_message": "x",
        },
    )
    assert resp.status_code == 422
