"""
NexusAgent LLM HTTP 客户端 — 首次真实 API 调用

使用标准库 urllib 发送 OpenAI 兼容 Chat Completions 请求。
支持 Mock 离线模式（CI / 无 Key 环境）与可注入 transport（单元测试）。

需求：ZL-NA-REQ-012

运行示例：
    NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py

作者：NexusAgent 项目组
创建日期：2026-07-17
版本：0.1.0
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.exceptions import APIError, ConfigError
from core.paths import get_path
from llm.env import LLMEnvConfig, load_llm_env
from llm.response import ChatCompletionResult, parse_chat_completion
from models import ChatMessage, ModelConfig

# transport(url, headers, payload) -> response dict
TransportFunc = Callable[[str, dict[str, str], dict[str, Any]], dict]


def build_request_body(
    messages: list[ChatMessage],
    config: ModelConfig,
) -> dict[str, Any]:
    """
    组装 Chat Completions 请求体。

    校验所有 ChatMessage 与 ModelConfig。
    """
    for msg in messages:
        msg.ensure_valid()
    body = config.to_api_params()
    body["messages"] = [m.to_api_message() for m in messages]
    return body


def default_transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict:
    """使用 urllib 发送 POST JSON 请求"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise APIError(
            f"HTTP 请求失败: {exc.reason}",
            status_code=exc.code,
            response_body=body,
        ) from exc
    except urllib.error.URLError as exc:
        raise APIError(f"网络连接失败: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise APIError(f"响应非合法 JSON: {exc}") from exc


def mock_transport_from_file(sample_path: Path) -> TransportFunc:
    """从本地 JSON 文件返回固定响应（离线 Mock）"""

    def _transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict:
        if not sample_path.exists():
            raise APIError(f"Mock 样本不存在: {sample_path}")
        return json.loads(sample_path.read_text(encoding="utf-8"))

    return _transport


class LLMClient:
    """
    大模型 Chat Completions 客户端

    Attributes:
        config: ModelConfig 调用参数
        env: LLMEnvConfig 连接配置
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        *,
        env: LLMEnvConfig | None = None,
        transport: TransportFunc | None = None,
        sample_path: Path | None = None,
    ) -> None:
        self.config = config or ModelConfig()
        self.config.ensure_valid()
        self.env = env or load_llm_env()
        self._sample_path = sample_path or get_path("chat_completion_sample")

        if transport is not None:
            self._transport = transport
        elif self.env.mock:
            self._transport = mock_transport_from_file(self._sample_path)
        else:
            self._transport = default_transport

    @classmethod
    def from_env(cls, **kwargs: Any) -> LLMClient:
        """从环境变量构造客户端"""
        return cls(env=load_llm_env(), **kwargs)

    def _headers(self) -> dict[str, str]:
        if self.env.mock:
            return {"Content-Type": "application/json"}
        if not self.env.api_key:
            raise ConfigError("非 Mock 模式需要 DEEPSEEK_API_KEY")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.env.api_key}",
        }

    def complete(self, messages: list[ChatMessage]) -> ChatCompletionResult:
        """
        发送 Chat Completions 请求并解析响应。

        Args:
            messages: ChatMessage 列表（含 system/user/assistant）

        Returns:
            ChatCompletionResult 含 assistant 消息与 token 统计
        """
        body = build_request_body(messages, self.config)
        raw = self._transport(self.env.chat_completions_url, self._headers(), body)
        return parse_chat_completion(raw)

    def chat(self, user_content: str, *, system_prompt: str | None = None) -> ChatMessage:
        """
        便捷方法：单轮 user 提问，返回 assistant 回复。

        Args:
            user_content: 用户消息正文
            system_prompt: 可选 system 提示词
        """
        messages: list[ChatMessage] = []
        if system_prompt:
            messages.append(ChatMessage("system", system_prompt))
        messages.append(ChatMessage("user", user_content))
        result = self.complete(messages)
        return result.message
