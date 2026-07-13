"""Day 23 FastAPI Chat API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from api.response_parser import classify_reply
from api.sessions import SessionManager


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.45.0"


def test_chat_faq_direct(client):
    resp = client.post("/api/chat", json={"message": "投资有风险吗"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kind"] == "faq"
    assert "FAQ" in data["reply"] or "风险" in data["reply"]
    assert "session_id" in data


def test_chat_route_or_llm(client):
    resp = client.post("/api/chat", json={"message": "根据资料查询收益率"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kind"] in ("route", "llm", "faq")
    assert len(data["reply"]) > 0


def test_chat_doc_summary(client):
    resp = client.post("/api/chat", json={"message": "帮我总结要点"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kind"] in ("route", "llm", "faq")


def test_chat_empty_validation(client):
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 422


def test_chat_session_id_preserved(client):
    r1 = client.post("/api/chat", json={"message": "你好", "session_id": "sess-a"})
    r2 = client.post("/api/chat", json={"message": "再见", "session_id": "sess-a"})
    assert r1.json()["session_id"] == "sess-a"
    assert r2.json()["session_id"] == "sess-a"


def test_classify_reply_faq():
    kind, meta = classify_reply("[FAQ 直答·70%] 投资有风险")
    assert kind == "faq"
    assert "FAQ" in meta


def test_classify_reply_route():
    kind, meta = classify_reply("[路由: rag_qa] 根据资料…")
    assert kind == "route"
    assert "rag_qa" in meta


def test_classify_reply_llm():
    kind, _ = classify_reply("这是一段普通回复")
    assert kind == "llm"


def test_session_manager_isolation():
    mgr = SessionManager()
    s1, o1 = mgr.get_or_create("user-1")
    s2, o2 = mgr.get_or_create("user-2")
    assert s1 != s2
    assert o1 is not o2


def test_frontend_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "NexusAgent" in resp.text


def test_config_js_present(client):
    resp = client.get("/config.js")
    assert resp.status_code == 200
    assert "NexusConfig" in resp.text
