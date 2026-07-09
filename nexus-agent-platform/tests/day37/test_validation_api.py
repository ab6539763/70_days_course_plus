"""Day 37 Validation API 测试。"""

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


def test_get_validation_config_default(client):
    data = client.get("/api/knowledge/validation-config").json()
    assert data["enabled"] is True
    assert data["min_score"] == 0.35


def test_put_validation_config(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "strict",
            "min_score": 0.5,
            "refuse_on_fail": False,
            "retry_on_fail": False,
            "max_retries": 0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "strict"


def test_validation_preview_fail(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "年化收益怎么样",
            "reply": "今天天气晴朗。",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is False


def test_validation_preview_pass(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True


def test_status_includes_validation_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.41.0"
    assert status["validation_config"]["enabled"] is True


def test_chat_includes_validation(client):
    resp = client.post("/api/chat", json={"message": "客服电话多少？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert "passed" in body["validation"]


def test_chat_refuses_on_fail(client):
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
    # Mock LLM 固定返回年化收益文案，与「chunk 分块」类引用不匹配 → 应拒答
    resp = client.post("/api/chat", json={"message": "智链科技总部在哪"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("validation")
    assert body["validation"]["passed"] is False
    assert body["validation"]["refused"] is True
    assert body["reply"].startswith("[校验未通过]")


def test_invalid_validation_mode_422(client):
    resp = client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "invalid",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": False,
            "max_retries": 1,
        },
    )
    assert resp.status_code == 422


def test_validation_preview_with_explicit_citations(client):
    resp = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "测试",
            "reply": "理财产品有风险",
            "citations": [
                {
                    "rank": 1,
                    "source": "risk.md",
                    "preview": "理财产品存在投资风险",
                    "matched_tokens": ["风险"],
                    "score": 0.9,
                    "chunk_id": "x1",
                }
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
