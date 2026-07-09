"""Day 24 Sprint 3 完整整合测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
REPO = SRC.parent.parent
FRONTEND = REPO / "frontend"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from day24.constants import DEMO_QUERIES
from day24.e2e_smoke import run_smoke


@pytest.fixture
def client():
    return TestClient(create_app())


def test_e2e_smoke_runner():
    assert run_smoke() == 0


def test_health_version_024(client):
    data = client.get("/api/health").json()
    assert data["version"] == "0.42.0"


def test_session_reset_endpoint(client):
    sid = "test-reset-session"
    client.post("/api/chat", json={"message": "你好", "session_id": sid})
    resp = client.post("/api/session/reset", json={"session_id": sid})
    assert resp.status_code == 200
    assert resp.json()["cleared"] is True


def test_chat_with_session_id(client):
    resp = client.post(
        "/api/chat",
        json={"message": "投资有风险吗", "session_id": "user-xyz"},
    )
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "user-xyz"


def test_demo_queries_all_200(client):
    for q in DEMO_QUERIES:
        r = client.post("/api/chat", json={"message": q, "session_id": "demo"})
        assert r.status_code == 200, q


def test_frontend_session_js(client):
    text = client.get("/session.js").text
    assert "NexusSession" in text
    assert "localStorage" in text


def test_frontend_errors_js(client):
    text = client.get("/errors.js").text
    assert "mapApiError" in text
    assert "502" in text


def test_index_has_new_chat_button():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    assert 'id="new-chat-btn"' in html
    assert "session.js" in html
    assert "errors.js" in html


def test_index_session_label():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    assert 'id="session-label"' in html


def test_mock_sends_session_id():
    mock = (FRONTEND / "mock.js").read_text(encoding="utf-8")
    assert "session_id" in mock
    assert "NexusSession" in mock


def test_sprint3_demo_script_exists():
    script = REPO / "scripts" / "sprint3_demo.sh"
    assert script.is_file()
    assert "e2e_smoke" in script.read_text(encoding="utf-8")


def test_sprint3_review_importable():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sprint3_review_test", SRC / "day24" / "sprint3_review.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
