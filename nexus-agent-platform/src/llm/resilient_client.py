"""
带重试与超时的 LLM 客户端

在 LLMClient 基础上为 complete 方法应用 RetryPolicy。

需求：ZL-NA-REQ-013
"""

from __future__ import annotations

from typing import Any

from llm.client import LLMClient, TransportFunc
from llm.env import LLMEnvConfig
from llm.response import ChatCompletionResult
from llm.retry import RetryPolicy, retry, with_timeout
from models import ChatMessage, ModelConfig


class ResilientLLMClient(LLMClient):
    """
    具备重试与超时保护的 LLM 客户端

    complete() 在瞬时 APIError（429/5xx/网络）时指数退避重试。
    ConfigError / ModelValidationError 立即失败，不重试。
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        *,
        env: LLMEnvConfig | None = None,
        transport: TransportFunc | None = None,
        policy: RetryPolicy | None = None,
        on_retry_log: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(config, env=env, transport=transport, **kwargs)
        self.policy = policy or RetryPolicy()
        self._on_retry_log = on_retry_log
        self._complete_resilient = self._build_resilient_complete()

    def _build_resilient_complete(self):
        on_retry = self._log_retry if self._on_retry_log else None

        @retry(
            max_attempts=self.policy.max_attempts,
            base_delay=self.policy.base_delay,
            backoff_factor=self.policy.backoff_factor,
            max_delay=self.policy.max_delay,
            on_retry=on_retry,
        )
        @with_timeout(self.policy.timeout_seconds)
        def _call(messages: list[ChatMessage]) -> ChatCompletionResult:
            return super(ResilientLLMClient, self).complete(messages)

        return _call

    def _log_retry(self, attempt: int, exc: BaseException, sleep_for: float) -> None:
        code = getattr(exc, "status_code", None)
        code_str = f" HTTP {code}" if code else ""
        print(
            f"  ⏳ 重试 {attempt}/{self.policy.max_attempts - 1}: "
            f"{exc}{code_str}，{sleep_for:.1f}s 后重试"
        )

    def complete(self, messages: list[ChatMessage]) -> ChatCompletionResult:
        return self._complete_resilient(messages)
