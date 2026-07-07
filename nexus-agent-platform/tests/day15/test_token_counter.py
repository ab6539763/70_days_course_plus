"""Day 15 Token 计数器测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from llm.response import ChatCompletionResult
from llm.token_counter import (
    TokenCounter,
    TokenSessionTracker,
    TokenUsage,
    estimate_messages_tokens,
    estimate_tokens,
)
from models import ChatMessage, ModelConfig

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "回复"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
}


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_chinese():
    n = estimate_tokens("你好世界")
    assert n >= 4


def test_estimate_tokens_english():
    n = estimate_tokens("hello world")
    assert n >= 2


def test_estimate_messages():
    msgs = [ChatMessage("user", "你好"), ChatMessage("assistant", "hi")]
    total = estimate_messages_tokens(msgs)
    assert total > estimate_tokens("你好")


def test_token_usage_from_dict():
    u = TokenUsage.from_usage_dict({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
    assert u.total_tokens == 15


def test_token_counter_cost():
    counter = TokenCounter(input_price_per_m=1.0, output_price_per_m=2.0)
    usage = TokenUsage(prompt_tokens=1_000_000, completion_tokens=500_000)
    cost = counter.estimate_cost(usage)
    assert abs(cost.input_cost - 1.0) < 0.001
    assert abs(cost.output_cost - 1.0) < 0.001


def test_session_tracker_accumulates():
    tracker = TokenSessionTracker()
    result = ChatCompletionResult(
        message=ChatMessage("assistant", "x"),
        model="deepseek-chat",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
    msgs = [ChatMessage("user", "hi")]
    tracker.record_turn(result, msgs)
    assert tracker.stats.turns == 1
    assert tracker.stats.total_tokens == 15


def test_session_summary():
    tracker = TokenSessionTracker()
    result = ChatCompletionResult(
        message=ChatMessage("assistant", "x"),
        model="deepseek-chat",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
    tracker.record_turn(result, [ChatMessage("user", "a")])
    assert "15" in tracker.summary()


def test_assistant_tokens_command():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    a = ChatAssistant(client=client, track_tokens=True)
    a.run_scripted(["你好"])
    handled, msg, _ = a.handle_command("/tokens")
    assert handled
    assert "120" in msg or "tokens" in msg


def test_assistant_shows_token_in_output():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    a = ChatAssistant(client=client, track_tokens=True)
    outputs = a.run_scripted(["测试"])
    assert any("tokens" in o for o in outputs)


def test_usage_format_line():
    u = TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3)
    assert "输入=1" in u.format_line()


def test_compare_estimate():
    counter = TokenCounter()
    usage = TokenUsage(prompt_tokens=50, estimated_prompt=40)
    text = counter.compare_estimate(usage)
    assert "+10" in text or "偏差" in text
