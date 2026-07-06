"""Day 8 ChatMessage 与 MessageHistory 测试。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DAY08 = SRC / "day08"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from models.message import ChatMessage, VALID_ROLES


def _load_history():
    spec = importlib.util.spec_from_file_location("msg_hist_test", DAY08 / "message_history.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["msg_hist_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def History():
    return _load_history().MessageHistory


def test_create_message():
    msg = ChatMessage("user", "你好")
    assert msg.role == "user"
    assert msg.content == "你好"
    assert msg.validate() is None


def test_invalid_role():
    msg = ChatMessage("bot", "hi")
    assert msg.validate() is not None


def test_empty_content():
    msg = ChatMessage("user", "   ")
    assert msg.validate() is not None


def test_to_dict_roundtrip():
    msg = ChatMessage("assistant", "回复", created_at="2026-01-01T00:00:00Z")
    restored = ChatMessage.from_dict(msg.to_dict())
    assert restored == msg


def test_to_api_message():
    msg = ChatMessage("user", "test")
    api = msg.to_api_message()
    assert api == {"role": "user", "content": "test"}
    assert "created_at" not in api


def test_from_api_response():
    parsed = {"role": "assistant", "content": "答案"}
    msg = ChatMessage.from_api_response(parsed)
    assert msg.is_assistant()
    assert msg.content == "答案"


def test_role_helpers():
    assert ChatMessage("system", "s").is_system()
    assert ChatMessage("user", "u").is_user()
    assert ChatMessage("assistant", "a").is_assistant()


def test_format_line_truncation():
    long_text = "x" * 100
    line = ChatMessage("user", long_text).format_line(max_content_len=20)
    assert line.endswith("...")


def test_history_add(History):
    h = History()
    assert h.add_user("你好") is None
    assert len(h) == 1
    assert h.last().is_user()


def test_history_reject_invalid(History):
    h = History()
    err = h.add(ChatMessage("invalid", "x"))
    assert err is not None


def test_history_api_export(History):
    h = History()
    h.add_system("你是助手")
    h.add_user("问题")
    api = h.to_api_messages()
    assert len(api) == 2
    assert api[0]["role"] == "system"


def test_history_save_load(History, tmp_path):
    path = tmp_path / "msgs.json"
    h = History()
    h.add_user("持久化测试")
    h.save_json(path)
    loaded = History.load_json(path)
    assert len(loaded) == 1
    assert loaded.last().content == "持久化测试"


def test_contact_class():
    spec = importlib.util.spec_from_file_location("contact_cls", DAY08 / "contact_class.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    c = mod.Contact(1, "张三", "13800138000", "a@b.com")
    assert c.validate() is None
    d = c.to_dict()
    assert mod.Contact.from_dict(d).name == "张三"
