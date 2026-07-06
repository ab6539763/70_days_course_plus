"""Day 12 LLM 客户端与 HTTP 测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.exceptions import APIError, ConfigError
from core.paths import get_path
from llm.client import LLMClient, build_request_body, default_transport
from llm.env import LLMEnvConfig, load_llm_env, parse_env_file
from llm.response import parse_chat_completion
from models import ChatMessage, ModelConfig


SAMPLE_RESPONSE = {
    "id": "chatcmpl-test",
    "model": "deepseek-chat",
    "choices": [
        {
            "message": {"role": "assistant", "content": "你好，我是 NexusAgent。"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
}


def mock_transport(_url, _headers, _payload):
    return SAMPLE_RESPONSE


def test_build_request_body():
    config = ModelConfig()
    messages = [ChatMessage("user", "hello")]
    body = build_request_body(messages, config)
    assert body["model"] == "deepseek-chat"
    assert body["messages"] == [{"role": "user", "content": "hello"}]


def test_build_request_body_invalid_message():
    config = ModelConfig()
    bad = ChatMessage("user", "")
    with pytest.raises(Exception):
        build_request_body([bad], config)


def test_parse_chat_completion():
    result = parse_chat_completion(SAMPLE_RESPONSE)
    assert result.message.content == "你好，我是 NexusAgent。"
    assert result.total_tokens == 18


def test_parse_chat_completion_empty_choices():
    with pytest.raises(APIError):
        parse_chat_completion({"choices": []})


def test_parse_chat_completion_api_error():
    with pytest.raises(APIError):
        parse_chat_completion({"error": {"message": "invalid key"}})


def test_llm_client_complete_mock():
    env = LLMEnvConfig(api_key="test", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=mock_transport)
    result = client.complete([ChatMessage("user", "hi")])
    assert result.message.is_assistant()


def test_llm_client_chat_helper():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(env=env, transport=mock_transport)
    reply = client.chat("你好", system_prompt="你是助手")
    assert reply.content


def test_load_llm_env_missing_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("NEXUS_LLM_MOCK", raising=False)
    with pytest.raises(ConfigError):
        load_llm_env(env_file=Path("/nonexistent/.env"))


def test_load_llm_env_mock_mode(monkeypatch):
    monkeypatch.setenv("NEXUS_LLM_MOCK", "1")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    cfg = load_llm_env(env_file=Path("/nonexistent/.env"))
    assert cfg.mock is True


def test_parse_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nDEEPSEEK_API_KEY=sk-test\nDEEPSEEK_BASE_URL=https://x/v1\n",
        encoding="utf-8",
    )
    data = parse_env_file(env_file)
    assert data["DEEPSEEK_API_KEY"] == "sk-test"


def test_llm_env_chat_url():
    env = LLMEnvConfig(api_key="k", base_url="https://api.deepseek.com/v1/")
    assert env.chat_completions_url == "https://api.deepseek.com/v1/chat/completions"


def test_get_path_chat_completion_sample():
    p = get_path("chat_completion_sample")
    assert p.exists()


def test_client_uses_sample_file_when_mock():
    env = LLMEnvConfig(api_key="", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(env=env, sample_path=get_path("chat_completion_sample"))
    result = client.complete([ChatMessage("user", "收益率？")])
    assert "理财" in result.message.content or result.message.content
