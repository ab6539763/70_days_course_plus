"""
LLM 流式输出（SSE）模块

解析 OpenAI 兼容的 Server-Sent Events 流，逐 delta 回调并汇总完整回复。
Day 16 仍使用标准库 urllib；异步版见 day16/async_stream_demos.py 预习。

需求：ZL-NA-REQ-016

作者：NexusAgent 项目组
创建日期：2026-07-21
版本：0.1.0
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.exceptions import APIError
from core.paths import get_path
from llm.client import LLMClient, build_request_body
from llm.token_counter import TokenUsage
from models import ChatMessage, ModelConfig

# transport(url, headers, payload) -> Iterator[dict]  每个 dict 为一个 chunk JSON
StreamTransportFunc = Callable[[str, dict[str, str], dict[str, Any]], Iterator[dict]]

DeltaCallback = Callable[[str], None]


@dataclass
class StreamChunk:
    """单个流式 chunk 解析结果"""

    delta_content: str = ""
    finish_reason: str = ""
    model: str = "unknown"
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class StreamCompletionResult:
    """流式调用汇总结果"""

    message: ChatMessage
    model: str
    finish_reason: str = ""
    chunk_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def usage_summary(self) -> str:
        return (
            f"tokens: prompt={self.prompt_tokens}, "
            f"completion={self.completion_tokens}, total={self.total_tokens}, "
            f"chunks={self.chunk_count}"
        )


def build_stream_request_body(
    messages: list[ChatMessage],
    config: ModelConfig,
) -> dict[str, Any]:
    """组装 stream=True 的请求体"""
    body = build_request_body(messages, config)
    body["stream"] = True
    return body


def parse_sse_line(line: str) -> dict[str, Any] | None:
    """
    解析单行 SSE。

    Returns:
        chunk dict；[DONE] 返回 {"done": True}；空行/注释返回 None
    """
    line = line.strip()
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if data == "[DONE]":
        return {"done": True}
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise APIError(f"SSE JSON 解析失败: {exc}") from exc


def parse_stream_chunk(data: dict[str, Any]) -> StreamChunk:
    """解析 chat.completion.chunk JSON 对象"""
    if data.get("done"):
        return StreamChunk(raw=data)

    choices = data.get("choices", [])
    delta_content = ""
    finish_reason = ""
    if choices:
        first = choices[0]
        delta = first.get("delta", {}) or {}
        delta_content = delta.get("content") or ""
        finish_reason = first.get("finish_reason") or ""

    return StreamChunk(
        delta_content=delta_content,
        finish_reason=finish_reason,
        model=data.get("model", "unknown"),
        raw=data,
    )


class StreamAccumulator:
    """累积 delta 内容为完整字符串"""

    def __init__(self) -> None:
        self._parts: list[str] = []

    def feed(self, chunk: StreamChunk) -> str:
        if chunk.delta_content:
            self._parts.append(chunk.delta_content)
        return chunk.delta_content

    @property
    def content(self) -> str:
        return "".join(self._parts)

    def reset(self) -> None:
        self._parts.clear()


def iter_sse_events(lines: Iterator[str]) -> Iterator[dict[str, Any]]:
    """从文本行迭代解析 SSE 事件"""
    for line in lines:
        parsed = parse_sse_line(line)
        if parsed is not None:
            yield parsed


def default_stream_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> Iterator[dict]:
    """urllib 流式 POST，逐行读取 SSE"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8")
                parsed = parse_sse_line(line)
                if parsed is None:
                    continue
                if parsed.get("done"):
                    break
                yield parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise APIError(
            f"流式 HTTP 失败: {exc.reason}",
            status_code=exc.code,
            response_body=body,
        ) from exc
    except urllib.error.URLError as exc:
        raise APIError(f"流式网络失败: {exc.reason}") from exc


def mock_stream_from_sse_file(path: Path) -> StreamTransportFunc:
    """从本地 .sse 文件模拟流式响应"""

    def _transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> Iterator[dict]:
        if not path.exists():
            raise APIError(f"Mock SSE 文件不存在: {path}")
        lines = path.read_text(encoding="utf-8").splitlines()
        for event in iter_sse_events(iter(lines)):
            if event.get("done"):
                break
            yield event

    return _transport


def mock_stream_from_text(text: str, *, model: str = "deepseek-chat") -> StreamTransportFunc:
    """将文本拆分为逐字符 chunk 的 Mock transport"""

    def _transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> Iterator[dict]:
        for ch in text:
            yield {
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [{"index": 0, "delta": {"content": ch}, "finish_reason": None}],
            }
        yield {
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": max(len(text), 1),
                "total_tokens": 10 + max(len(text), 1),
            },
        }

    return _transport


class StreamingLLMClient(LLMClient):
    """
    支持流式 complete 的 LLM 客户端

    非 Mock 模式使用 default_stream_transport；
    Mock 模式默认读取 llm/sample_data/stream_mock.sse。
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        *,
        stream_transport: StreamTransportFunc | None = None,
        sse_sample_path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(config, **kwargs)
        self._sse_sample_path = sse_sample_path or get_path("stream_mock_sse")

        if stream_transport is not None:
            self._stream_transport = stream_transport
        elif self.env.mock:
            self._stream_transport = mock_stream_from_sse_file(self._sse_sample_path)
        else:
            self._stream_transport = default_stream_transport

    def stream_complete(
        self,
        messages: list[ChatMessage],
        *,
        on_delta: DeltaCallback | None = None,
    ) -> StreamCompletionResult:
        """
        流式 Chat Completions：逐 delta 回调，返回汇总结果。

        Args:
            messages: 对话历史
            on_delta: 每收到 content delta 时调用（用于 print 打字机效果）
        """
        body = build_stream_request_body(messages, self.config)
        accumulator = StreamAccumulator()
        model = self.config.model
        finish_reason = ""
        chunk_count = 0
        usage = TokenUsage()

        for raw_chunk in self._stream_transport(
            self.env.chat_completions_url,
            self._headers(),
            body,
        ):
            chunk_count += 1
            parsed = parse_stream_chunk(raw_chunk)
            if parsed.model != "unknown":
                model = parsed.model
            delta = accumulator.feed(parsed)
            if delta and on_delta:
                on_delta(delta)
            if parsed.finish_reason:
                finish_reason = parsed.finish_reason

            usage_raw = raw_chunk.get("usage")
            if usage_raw:
                usage = TokenUsage.from_usage_dict(usage_raw)

        content = accumulator.content
        if not content:
            raise APIError("流式响应未产生任何 content")

        message = ChatMessage("assistant", content)
        return StreamCompletionResult(
            message=message,
            model=model,
            finish_reason=finish_reason,
            chunk_count=chunk_count,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    def stream_chat(
        self,
        user_content: str,
        *,
        system_prompt: str | None = None,
        on_delta: DeltaCallback | None = None,
    ) -> StreamCompletionResult:
        """便捷流式单轮对话"""
        messages: list[ChatMessage] = []
        if system_prompt:
            messages.append(ChatMessage("system", system_prompt))
        messages.append(ChatMessage("user", user_content))
        return self.stream_complete(messages, on_delta=on_delta)


def collect_stream_text(
    client: StreamingLLMClient,
    messages: list[ChatMessage],
    *,
    on_delta: DeltaCallback | None = None,
) -> str:
    """流式调用并仅返回文本（工具函数）"""
    return client.stream_complete(messages, on_delta=on_delta).message.content
