"""Day 14 cli_assistant 多轮对话测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant, DEFAULT_SYSTEM_PROMPT
from core.exceptions import APIError
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ChatMessage, ModelConfig
from services import MessageHistory

SAMPLE_RESPONSE = {
    "model": "deepseek-chat",
    "choices": [
        {"message": {"role": "assistant", "content": "我是 NexusAgent 助手。"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

FOLLOWUP_RESPONSE = {
    "model": "deepseek-chat",
    "choices": [
        {"message": {"role": "assistant", "content": "年化约 3.5%-4.2%。"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28},
}


def make_mock_client(responses: list[dict] | None = None):
    responses = list(responses or [SAMPLE_RESPONSE])
    state = {"i": 0}

    def transport(_url, _headers, _payload):
        idx = min(state["i"], len(responses) - 1)
        state["i"] += 1
        return responses[idx]

    env = LLMEnvConfig(api_key="test", base_url="https://api.example.com/v1", mock=True)
    return LLMClient(ModelConfig(), env=env, transport=transport)


def test_assistant_has_default_system():
    a = ChatAssistant(client=make_mock_client())
    assert a._has_system_message()
    assert a.history.messages[0].role == "system"


def test_handle_help_command():
    a = ChatAssistant(client=make_mock_client(), system_prompt="")
    handled, msg, exit_ = a.handle_command("/help")
    assert handled and not exit_
    assert "/exit" in msg


def test_handle_exit_command():
    a = ChatAssistant(client=make_mock_client(), system_prompt="")
    handled, msg, exit_ = a.handle_command("/exit")
    assert handled and exit_


def test_clear_keeps_system():
    a = ChatAssistant(client=make_mock_client())
    a.history.add_user("hello")
    handled, _, _ = a.handle_command("/clear")
    assert handled
    assert len(a.history.messages) == 1
    assert a.history.messages[0].role == "system"


def test_chat_turn_mock():
    a = ChatAssistant(client=make_mock_client())
    reply = a.chat_turn("你好")
    assert "NexusAgent" in reply
    assert len(a.history.messages) >= 3  # system, user, assistant


def test_run_scripted_multi_turn():
    a = ChatAssistant(
        client=make_mock_client([SAMPLE_RESPONSE, FOLLOWUP_RESPONSE]),
    )
    outputs = a.run_scripted(["你好", "收益率？"])
    assert any("NexusAgent" in o for o in outputs)
    assert any("3.5" in o or "助手" in o for o in outputs)


def test_run_scripted_exit():
    a = ChatAssistant(client=make_mock_client())
    outputs = a.run_scripted(["/exit"])
    assert any("再见" in o for o in outputs)


def test_save_and_load_history(tmp_path):
    path = tmp_path / "session.json"
    a = ChatAssistant(client=make_mock_client(), history_path=path)
    a.chat_turn("测试")
    a.save_history()
    assert path.exists()

    b = ChatAssistant(client=make_mock_client(), history_path=path)
    b.load_history()
    assert len(b.history.messages) >= 2


def test_api_error_handled_in_scripted():
    def fail_transport(*_args):
        raise APIError("503", status_code=503)

    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=fail_transport)
    a = ChatAssistant(client=client)
    outputs = a.run_scripted(["你好"])
    assert any("API" in o or "失败" in o for o in outputs)


def test_system_command():
    a = ChatAssistant(client=make_mock_client(), system_prompt="")
    handled, msg, _ = a.handle_command("/system 你是测试助手")
    assert handled
    assert any(m.content == "你是测试助手" for m in a.history.messages if m.role == "system")


def test_empty_input_chat_turn():
    a = ChatAssistant(client=make_mock_client())
    assert "有效" in a.chat_turn("   ")


def test_is_command():
    a = ChatAssistant(client=make_mock_client())
    assert a.is_command("/help")
    assert not a.is_command("hello")
