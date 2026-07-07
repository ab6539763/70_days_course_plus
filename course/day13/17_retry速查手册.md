# retry 速查手册

**模块**：`nexus-agent-platform/src/llm/retry.py`  
**需求**：ZL-NA-REQ-013

---

## 快速开始

```python
from core.exceptions import APIError
from llm.retry import retry, with_timeout, RetryPolicy, is_retryable_error

@retry(max_attempts=3, base_delay=1.0, backoff_factor=2.0)
def call_flaky_api():
    ...

@with_timeout(30.0)
def slow_job():
    ...
```

---

## is_retryable_error

```python
def is_retryable_error(exc: BaseException) -> bool
```

| 输入 | 输出 |
|------|------|
| `ConfigError` | `False` |
| `ModelValidationError` | `False` |
| `APIError(429)` | `True` |
| `APIError(503)` | `True` |
| `APIError(401)` | `False` |
| `APIError()` 无 code | `True` |
| 其他 | `False` |

---

## RetryPolicy

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 30.0
    timeout_seconds: float = 60.0
```

---

## retry

```python
def retry(
    max_attempts: int = 3,
    *,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    retryable: Callable[[BaseException], bool] | None = None,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]
```

**on_retry 签名**：`(attempt: int, exc: BaseException, sleep_for: float) -> None`

---

## with_timeout

```python
def with_timeout(seconds: float) -> Callable[[Callable[P, R]], Callable[P, R]]
```

- `seconds <= 0` → `ValueError`  
- 超时 → `APIError("调用超时（>Ns）")`

---

## api_retry

```python
def api_retry(policy: RetryPolicy | None = None, **kwargs)
```

等价于 `retry(..., retryable=is_retryable_error)` + Policy 字段。

---

## apply_resilience

```python
def apply_resilience(func, policy: RetryPolicy | None = None) -> Callable
```

顺序：`with_timeout` 内，`api_retry` 外。

---

## ResilientLLMClient 速用

```python
from llm.resilient_client import ResilientLLMClient
from llm.retry import RetryPolicy
from models import ChatMessage

client = ResilientLLMClient(
    policy=RetryPolicy(max_attempts=4, base_delay=0.5),
    on_retry_log=True,
)
result = client.complete([ChatMessage("user", "你好")])
```

Mock：

```bash
NEXUS_LLM_MOCK=1 python3 src/day13/resilient_client_demo.py
```

---

## 装饰顺序备忘

```python
# ✅ 正确
@retry(...)
@with_timeout(60)
def work(): ...

# ❌ 错误
@with_timeout(60)
@retry(...)
def work(): ...
```

---

## 命令行演示

```bash
python3 src/day13/retry_demos.py
python3 src/day13/decorator_demos.py
```

---

## 相关异常

来自 `core.exceptions`：

- `APIError` — 可带 `status_code`, `response_body`  
- `ConfigError` — 不重试  
- `ModelValidationError` — 不重试

---

*对照表：[18_与Day12客户端对照表.md](18_与Day12客户端对照表.md)*
