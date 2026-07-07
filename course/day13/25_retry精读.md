# Day 13 retry.py 精读

**文件**：`nexus-agent-platform/src/llm/retry.py`  
**行数**：约 163 行  
**建议**：对照源码逐段阅读，约 40 分钟

---

## 模块文档与导入（L1–26）

```python
"""
API 重试与超时装饰器
...
需求：ZL-NA-REQ-013
"""
from __future__ import annotations
import concurrent.futures
import functools
import time
...
P = ParamSpec("P")
R = TypeVar("R")
```

**精读笔记**：

- `from __future__ import annotations` 推迟注解求值，兼容前向引用  
- `ParamSpec` 保留被装饰函数参数类型（3.10+）  
- 仅依赖 `core.exceptions` 三种异常，无 llm 循环依赖

---

## DEFAULT_RETRYABLE_STATUS（L28–29）

```python
DEFAULT_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
```

**为何 frozenset**：哈希、不可变，适合模块级常量；`in` 测试 O(1)。

**扩展点**：企业可增加 408，需同步测试与文档。

---

## is_retryable_error（L32–48）

完整逻辑三遍阅读法：

1. **第一遍**：非 APIError 领域错误 → False  
2. **第二遍**：APIError 无 code → True（网络）  
3. **第三遍**：有 code → 白名单内 True，否则 False（含 401）

**边界用例**：

```python
is_retryable_error(APIError("x", status_code=404))  # False
is_retryable_error(ConfigError("no key"))           # False
is_retryable_error(APIError("timeout msg"))         # True, code None
```

---

## RetryPolicy（L51–63）

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    ...
    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts 必须 >= 1")
```

**设计**：数据与行为分离——Policy 可序列化、可来自配置文件（未来）。

`timeout_seconds` 在 Policy 中但由 `with_timeout` 消费，非 `retry` 字段。

---

## retry 装饰器工厂（L66–114）

### 工厂参数校验（L87–88）

与 `RetryPolicy` 双重校验，防止直接 `@retry(0)`。

### predicate（L90）

```python
predicate = retryable or is_retryable_error
```

依赖注入判定函数，单元测试可传 `lambda e: True` 测纯退避。

### 核心循环（L97–110）

| 行 | 语义 |
|----|------|
| L97 | attempt 从 1 到 max_attempts **含** |
| L99 | 成功则立即 return |
| L102–103 | 不可重试或最后一次 → raise |
| L104 | `min(delay, max_delay)` cap |
| L105–106 | 可选 on_retry |
| L107 | **阻塞** sleep |
| L108 | 指数倍增 delay |

### assert last_exc（L109–110）

理论不可达（循环内必 return 或 raise），满足类型检查器。

### functools.wraps（L93）

必考点。

---

## with_timeout（L117–139）

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    future = pool.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=seconds)
    except concurrent.futures.TimeoutError as exc:
        raise APIError(f"调用超时（>{seconds}s）") from exc
```

**精读问题**：

1. 为何 `max_workers=1`？单调用单线程，简单隔离。  
2. 为何转 `APIError`？与 HTTP 错误统一，进入 `is_retryable_error`。  
3. `seconds <= 0` 在 L124 拒绝。

---

## api_retry（L142–152）

语法糖：

```python
return retry(
    max_attempts=policy.max_attempts,
    ...
    retryable=is_retryable_error,
)
```

固定 `retryable`，避免业务误传。

---

## apply_resilience（L155–163）

```python
wrapped = with_timeout(policy.timeout_seconds)(func)
wrapped = api_retry(policy)(wrapped)
return wrapped
```

**顺序证明**：设 `func` 为裸 complete。

- 内：`f1 = with_timeout(func)` — 单次超时  
- 外：`f2 = api_retry(f1)` — 多次调用 f1  

每次 retry attempt 重新执行 `f1`，计时器重置。✓

---

## 与 resilient_client 的差异

| 项 | retry.py | resilient_client.py |
|----|----------|---------------------|
| 职责 | 通用装饰器 | LLM 专用集成 |
| on_retry | 参数传入 | `_log_retry` 可选 |
| 装饰时机 | 调用时/工具函数 | `__init__` 一次 |

---

## 自测题

1. 删除 L93 的 wraps 会影响什么？  
2. `on_retry` 第三个参数含义？  
3. 若 `backoff_factor=1` 退避形态？（固定间隔）  
4. `apply_resilience` 交换两行会怎样？（retry 在内，timeout 包不住每次 attempt）

---

*Lab：[26_实操Lab手册.md](26_实操Lab手册.md)*
