"""
LLM API 响应解析

复用 Day 5 解析逻辑，将 HTTP JSON 响应转为 ChatMessage 与统计信息。

需求：ZL-NA-REQ-012
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.exceptions import APIError
from models import ChatMessage


@dataclass
class ChatCompletionResult:
    """Chat Completion API 调用结果"""

    message: ChatMessage
    model: str
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw: dict = field(default_factory=dict, repr=False)

    def usage_summary(self) -> str:
        return (
            f"tokens: prompt={self.prompt_tokens}, "
            f"completion={self.completion_tokens}, total={self.total_tokens}"
        )


def parse_chat_completion(response: dict) -> ChatCompletionResult:
    """
    解析 OpenAI 兼容 Chat Completion 响应。

    Raises:
        APIError: 响应格式非法或 choices 为空
    """
    if not isinstance(response, dict):
        raise APIError("响应不是 JSON 对象")

    if response.get("error"):
        err = response["error"]
        if isinstance(err, dict):
            msg = err.get("message", str(err))
            code = err.get("code")
            raise APIError(f"API 返回错误: {msg}", status_code=code)
        raise APIError(f"API 返回错误: {err}")

    choices = response.get("choices", [])
    if not choices:
        raise APIError("响应缺少 choices 字段或为空")

    first = choices[0]
    message_data = first.get("message", {})
    if not message_data.get("content"):
        raise APIError("assistant 消息 content 为空")

    message = ChatMessage.from_api_response(message_data)
    usage = response.get("usage", {}) or {}

    return ChatCompletionResult(
        message=message,
        model=response.get("model", "unknown"),
        finish_reason=first.get("finish_reason") or "",
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
        total_tokens=int(usage.get("total_tokens", 0)),
        raw=response,
    )
