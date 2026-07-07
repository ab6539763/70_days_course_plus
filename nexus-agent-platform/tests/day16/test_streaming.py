"""Day 16 流式输出测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.exceptions import APIError
from core.paths import get_path
from llm.env import LLMEnvConfig
from llm.streaming import (
    StreamAccumulator,
    StreamingLLMClient,
    build_stream_request_body,
    mock_stream_from_text,
    parse_sse_line,
    parse_stream_chunk,
)
from models import ChatMessage, ModelConfig


def test_parse_sse_line_data():
    parsed = parse_sse_line('data: {"choices":[{"delta":{"content":"a"}}]}')
    assert parsed is not None
    assert "choices" in parsed


def test_parse_sse_line_done():
    assert parse_sse_line("data: [DONE]") == {"done": True}


def test_parse_sse_line_empty():
    assert parse_sse_line("") is None
    assert parse_sse_line(": ping") is None


def test_parse_stream_chunk_delta():
    chunk = parse_stream_chunk(
        {"choices": [{"delta": {"content": "你好"}, "finish_reason": None}], "model": "m"}
    )
    assert chunk.delta_content == "你好"
    assert chunk.model == "m"


def test_stream_accumulator():
    acc = StreamAccumulator()
    c1 = parse_stream_chunk({"choices": [{"delta": {"content": "A"}}]})
    c2 = parse_stream_chunk({"choices": [{"delta": {"content": "B"}}]})
    acc.feed(c1)
    acc.feed(c2)
    assert acc.content == "AB"


def test_build_stream_request_body():
    body = build_stream_request_body([ChatMessage("user", "hi")], ModelConfig())
    assert body["stream"] is True
    assert body["messages"][0]["role"] == "user"


def test_mock_stream_from_text():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = StreamingLLMClient(
        ModelConfig(),
        env=env,
        stream_transport=mock_stream_from_text("Hi"),
    )
    parts: list[str] = []
    result = client.stream_complete(
        [ChatMessage("user", "test")],
        on_delta=lambda d: parts.append(d),
    )
    assert result.message.content == "Hi"
    assert "".join(parts) == "Hi"
    assert result.chunk_count >= 2


def test_streaming_client_mock_sse_file():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = StreamingLLMClient(ModelConfig(), env=env)
    result = client.stream_complete([ChatMessage("user", "你好")])
    assert "NexusAgent" in result.message.content
    assert result.total_tokens > 0


def test_stream_chat_helper():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = StreamingLLMClient(
        ModelConfig(),
        env=env,
        stream_transport=mock_stream_from_text("OK"),
    )
    result = client.stream_chat("ping")
    assert result.message.content == "OK"


def test_empty_stream_raises():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)

    def empty_transport(*_args):
        yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}

    client = StreamingLLMClient(ModelConfig(), env=env, stream_transport=empty_transport)
    with pytest.raises(APIError, match="未产生"):
        client.stream_complete([ChatMessage("user", "x")])


def test_get_path_stream_mock_sse():
    p = get_path("stream_mock_sse")
    assert p.exists()


def test_usage_summary_includes_chunks():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = StreamingLLMClient(
        ModelConfig(),
        env=env,
        stream_transport=mock_stream_from_text("x"),
    )
    result = client.stream_complete([ChatMessage("user", "a")])
    assert "chunks=" in result.usage_summary()
