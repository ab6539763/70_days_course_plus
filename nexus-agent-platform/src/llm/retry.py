"""
API 重试与超时装饰器

为 LLMClient.complete 提供指数退避重试与超时保护。
Day 13 教学重点：装饰器工厂、functools.wraps、可重试异常判定。

需求：ZL-NA-REQ-013

作者：NexusAgent 项目组
创建日期：2026-07-18
版本：0.1.0
"""

from __future__ import annotations

import concurrent.futures
import functools
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

from core.exceptions import APIError, ConfigError, ModelValidationError

P = ParamSpec("P")
R = TypeVar("R")

# 默认可重试的 HTTP 状态码：限流 + 服务端瞬时故障
DEFAULT_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


def is_retryable_error(exc: BaseException) -> bool:
    """
    判断异常是否值得重试。

    不重试：ConfigError、ModelValidationError、4xx 客户端错误（除 429）。
    重试：429、5xx、无 status_code 的网络层 APIError。
    """
    if isinstance(exc, (ConfigError, ModelValidationError)):
        return False
    if isinstance(exc, APIError):
        code = exc.status_code
        if code is None:
            return True
        if code in DEFAULT_RETRYABLE_STATUS:
            return True
        return False
    return False


@dataclass
class RetryPolicy:
    """重试策略配置"""

    max_attempts: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 30.0
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts 必须 >= 1")


def retry(
    max_attempts: int = 3,
    *,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    retryable: Callable[[BaseException], bool] | None = None,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    重试装饰器工厂（带参数的装饰器）。

    Args:
        max_attempts: 最大尝试次数（含首次）
        base_delay: 首次重试前等待秒数
        backoff_factor: 指数退避倍数
        max_delay: 单次等待上限
        retryable: 自定义可重试判定，默认 is_retryable_error
        on_retry: 回调 (attempt, exc, sleep_seconds)
    """

    if max_attempts < 1:
        raise ValueError("max_attempts 必须 >= 1")

    predicate = retryable or is_retryable_error

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = base_delay
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except BaseException as exc:
                    last_exc = exc
                    if attempt >= max_attempts or not predicate(exc):
                        raise
                    sleep_for = min(delay, max_delay)
                    if on_retry:
                        on_retry(attempt, exc, sleep_for)
                    time.sleep(sleep_for)
                    delay *= backoff_factor
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def with_timeout(seconds: float) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    超时装饰器：在独立线程中执行函数，超时抛 APIError。

    适用于同步 urllib 调用包装；Day 16 流式输出将改用异步超时。
    """

    if seconds <= 0:
        raise ValueError("timeout seconds 必须为正数")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError as exc:
                    raise APIError(f"调用超时（>{seconds}s）") from exc

        return wrapper

    return decorator


def api_retry(policy: RetryPolicy | None = None, **kwargs) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """预设的 API 重试装饰器（使用 RetryPolicy 或关键字参数）"""
    if policy is None:
        policy = RetryPolicy(**kwargs)
    return retry(
        max_attempts=policy.max_attempts,
        base_delay=policy.base_delay,
        backoff_factor=policy.backoff_factor,
        max_delay=policy.max_delay,
        retryable=is_retryable_error,
    )


def apply_resilience(
    func: Callable[P, R],
    policy: RetryPolicy | None = None,
) -> Callable[P, R]:
    """组合超时 + 重试装饰器（内层超时，外层重试）"""
    policy = policy or RetryPolicy()
    wrapped = with_timeout(policy.timeout_seconds)(func)
    wrapped = api_retry(policy)(wrapped)
    return wrapped
