"""Day 38 Validation Retry API 测试。"""

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
    assert client.get("/api/health").json()["version"] == "0.40.0"


def test_validation_retry_preview(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "retries" in data
    assert data["passed"] is True


def test_validation_retry_preview_reports_route(client):
    resp = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "理财安全吗",
            "reply": "投资需谨慎，详见产品说明书风险提示。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("retry_route") is not None or data.get("retries", 0) >= 0


def test_put_validation_config_retry_fields(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["retry_on_fail"] is True
    assert body["max_retries"] == 2


def test_status_includes_validation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.40.0"
    assert status["validation_config"]["retry_on_fail"] is False


def test_chat_includes_validation_retries_field(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": False,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert "retries" in body["validation"]


def test_chat_refuses_after_retry_exhausted(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "strict",
            "min_score": 0.9,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    assert resp.status_code == 200
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) >= 1
    assert val.get("passed") is False
    assert val.get("refused") is True
    assert body["reply"].startswith("[校验未通过]")


def test_chat_retry_preserves_day37_when_disabled(client):
    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": False,
            "max_retries": 0,
        },
    )
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    body = resp.json()
    val = body.get("validation") or {}
    assert val.get("retries", 0) == 0
    assert val.get("refused") is True


def test_validation_preview_still_works(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
