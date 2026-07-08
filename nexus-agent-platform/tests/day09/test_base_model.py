"""Day 9 BaseModel 体系测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from models import BaseModel, ChatMessage, Contact, ModelConfig, ModelValidationError


def test_chat_message_is_base_model():
    msg = ChatMessage("user", "hi")
    assert isinstance(msg, BaseModel)
    assert msg.is_valid()


def test_contact_is_base_model():
    c = Contact(1, "张三", "13800138000", "a@b.com")
    assert isinstance(c, BaseModel)
    assert c.validate() is None


def test_model_config_validate():
    cfg = ModelConfig("deepseek-chat", 0.7, 1024)
    assert cfg.validate() is None
    bad = ModelConfig("", 3.0, -1)
    assert bad.validate() is not None


def test_ensure_valid_raises():
    bad = ChatMessage("bot", "x")
    with pytest.raises(ModelValidationError):
        bad.ensure_valid()


def test_to_json_ready():
    msg = ChatMessage("user", "持久化")
    d = msg.to_json_ready()
    assert d["content"] == "持久化"


def test_from_dict_safe_success():
    obj, err = ChatMessage.from_dict_safe({"role": "user", "content": "ok"})
    assert err is None
    assert obj is not None


def test_from_dict_safe_fail():
    obj, err = Contact.from_dict_safe({"id": 1, "name": "", "phone": "x", "email": "a@b.com"})
    assert obj is None
    assert err is not None


def test_model_config_api_params():
    cfg = ModelConfig("deepseek-chat", 0.5, 256)
    params = cfg.to_api_params()
    assert params["model"] == "deepseek-chat"
    assert params["temperature"] == 0.5


def test_polymorphism_list():
    items: list[BaseModel] = [
        ChatMessage("user", "a"),
        Contact(2, "王五", "13800138002", "w@b.com"),
        ModelConfig(),
    ]
    for item in items:
        assert item.validate() is None
    assert len([i.to_dict() for i in items]) == 3


def test_contact_invalid_id():
    c = Contact(0, "张三", "13800138000", "a@b.com")
    assert c.validate() is not None


def test_model_type_property():
    assert ChatMessage("user", "x").model_type == "ChatMessage"
