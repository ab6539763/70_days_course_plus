"""Day 22 前端静态聊天页测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
SRC = ROOT / "src"
FRONTEND = REPO / "frontend"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from day22.constants import REQUIRED_ELEMENT_IDS, REQUIRED_FILES
from day22.frontend_audit import audit_frontend


def test_frontend_directory_exists():
    assert FRONTEND.is_dir()


@pytest.mark.parametrize("filename", REQUIRED_FILES)
def test_required_files_exist(filename):
    assert (FRONTEND / filename).is_file()


@pytest.mark.parametrize("element_id", REQUIRED_ELEMENT_IDS)
def test_index_has_element_ids(element_id):
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    assert f'id="{element_id}"' in html


def test_index_loads_scripts():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    assert 'src="mock.js"' in html
    assert 'src="app.js"' in html


def test_mock_has_send_message():
    mock = (FRONTEND / "mock.js").read_text(encoding="utf-8")
    assert "function sendMessage" in mock or "async function sendMessage" in mock
    assert "NexusMock" in mock


def test_mock_faq_pattern():
    mock = (FRONTEND / "mock.js").read_text(encoding="utf-8")
    assert "FAQ 直答" in mock


def test_app_append_message():
    app = (FRONTEND / "app.js").read_text(encoding="utf-8")
    assert "appendMessage" in app
    assert "parseReply" in app


def test_css_bubble_styles():
    css = (FRONTEND / "style.css").read_text(encoding="utf-8")
    assert ".msg--user" in css
    assert ".msg--bot" in css
    assert ".msg__tag--faq" in css


def test_frontend_audit_passes():
    assert audit_frontend(FRONTEND) == []


def test_mock_api_placeholder():
    mock = (FRONTEND / "mock.js").read_text(encoding="utf-8")
    assert "/api/chat" in mock
    assert "sendMessageApi" in mock


def test_readme_has_serve_command():
    readme = (FRONTEND / "README.md").read_text(encoding="utf-8")
    assert "http.server" in readme
