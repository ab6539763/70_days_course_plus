"""Day 17 Prompt 模板库测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant
from core.exceptions import ConfigError
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ChatMessage, ModelConfig
from prompts import (
    DEFAULT_ASSISTANT,
    PromptRegistry,
    PromptTemplate,
    RAG_QA,
    default_registry,
    extract_variables,
)

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
}


def test_extract_variables():
    vars_ = extract_variables("Hello {name}, {role}")
    assert vars_ == ("name", "role")


def test_render_success():
    text = DEFAULT_ASSISTANT.render(company="智链科技")
    assert "智链科技" in text


def test_render_missing_var():
    with pytest.raises(ConfigError):
        DEFAULT_ASSISTANT.render()


def test_render_safe():
    result, err = DEFAULT_ASSISTANT.render_safe(company="X")
    assert err is None
    assert "X" in result


def test_to_system_message():
    msg = RAG_QA.to_system_message(company="C", context="资料")
    assert msg.role == "system"
    assert "资料" in msg.content


def test_preview_placeholders():
    preview = RAG_QA.preview(company="智链科技")
    assert "<context>" in preview


def test_registry_get_builtin():
    tmpl = default_registry.get("rag_qa")
    assert tmpl.name == "rag_qa"


def test_registry_unknown():
    reg = PromptRegistry()
    with pytest.raises(ConfigError):
        reg.get("not_exist")


def test_load_from_file(tmp_path):
    reg = PromptRegistry()
    f = tmp_path / "test_tmpl.txt"
    f.write_text("# 测试\n你好 {name}", encoding="utf-8")
    tmpl = reg.load_from_file(f)
    assert tmpl.render(name="Nexus") == "你好 Nexus"


def test_registry_loads_customer_service():
    assert "customer_service" in default_registry.list_names()


def test_assistant_apply_template():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    a = ChatAssistant(client=client, track_tokens=False)
    rendered = a.apply_template("default_assistant", variables={"company": "测试公司"})
    assert "测试公司" in rendered
    assert a.history.messages[0].role == "system"


def test_assistant_template_command_list():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    a = ChatAssistant(client=client, track_tokens=False)
    handled, msg, _ = a.handle_command("/template list")
    assert handled
    assert "rag_qa" in msg
