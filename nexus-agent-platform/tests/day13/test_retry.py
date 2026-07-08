"""Day 13 重试装饰器与 ResilientLLMClient 测试。"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.exceptions import APIError, ConfigError
from llm.env import LLMEnvConfig
from llm.resilient_client import ResilientLLMClient
from llm.retry import RetryPolicy, is_retryable_error, retry, with_timeout
from models import ChatMessage, ModelConfig

SAMPLE_RESPONSE = {
    "model": "deepseek-chat",
    "choices": [
        {"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def test_is_retryable_429():
    assert is_retryable_error(APIError("x", status_code=429))


def test_is_retryable_503():
    assert is_retryable_error(APIError("x", status_code=503))


def test_not_retryable_401():
    assert not is_retryable_error(APIError("x", status_code=401))


def test_not_retryable_config():
    assert not is_retryable_error(ConfigError("bad key"))


def test_retry_succeeds_after_failures():
    calls = {"n": 0}

    @retry(max_attempts=3, base_delay=0.01)
    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise APIError("503", status_code=503)
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_retry_exhausted():
    @retry(max_attempts=2, base_delay=0.01)
    def always_fail() -> None:
        raise APIError("503", status_code=503)

    with pytest.raises(APIError):
        always_fail()


def test_retry_no_retry_on_config_error():
    calls = {"n": 0}

    @retry(max_attempts=3, base_delay=0.01)
    def bad_config() -> None:
        calls["n"] += 1
        raise ConfigError("no key")

    with pytest.raises(ConfigError):
        bad_config()
    assert calls["n"] == 1


def test_with_timeout_success():
    @with_timeout(2.0)
    def fast() -> int:
        return 42

    assert fast() == 42


def test_with_timeout_raises():
    @with_timeout(0.1)
    def slow() -> None:
        time.sleep(0.5)

    with pytest.raises(APIError, match="超时"):
        slow()


def test_retry_policy_validation():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_resilient_client_retries_transport():
    calls = {"n": 0}

    def transport(_url, _headers, _payload):
        calls["n"] += 1
        if calls["n"] < 2:
            raise APIError("503", status_code=503)
        return SAMPLE_RESPONSE

    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    policy = RetryPolicy(max_attempts=3, base_delay=0.01, timeout_seconds=5)
    client = ResilientLLMClient(ModelConfig(), env=env, transport=transport, policy=policy)
    result = client.complete([ChatMessage("user", "hi")])
    assert result.message.content == "ok"
    assert calls["n"] == 2


def test_retry_preserves_function_name():
    @retry(max_attempts=2)
    def named_func() -> None:
        pass

    assert named_func.__name__ == "named_func"


def test_on_retry_callback():
    events: list[int] = []

    @retry(max_attempts=3, base_delay=0.01, on_retry=lambda a, e, s: events.append(a))
    def flaky() -> str:
        if len(events) < 1:
            raise APIError("429", status_code=429)
        return "done"

    assert flaky() == "done"
    assert events == [1]
