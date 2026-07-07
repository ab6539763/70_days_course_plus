# Day 13 实操 Lab 手册（Step-by-Step）

按步骤完成全天实验，约 3600 字。  
**环境**：`cd nexus-agent-platform` · `export PYTHONPATH=src`

---

## Lab 0：环境自检（5 分钟）

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 -c "from llm.retry import retry; from llm.resilient_client import ResilientLLMClient; print('OK')"
```

预期：打印 `OK`。

若失败：检查目录与 PYTHONPATH。

---

## Lab 1：装饰器基础（15 分钟）

```bash
python3 src/day13/decorator_demos.py
```

### 记录表

| 输出段 | 你观察到的值 |
|--------|--------------|
| greet 返回值 | |
| repeat 打印 tick 次数 | |
| `greet.__name__`（REPL 查看） | |

### REPL 追问

```python
from day13.decorator_demos import greet
greet.__name__  # 应为 greet
help(greet)     # 应有 docstring
```

`functools.wraps` 的作用？

<details><summary>提示</summary>保留原函数元数据</details>

---

## Lab 2：retry 与 429（20 分钟）

```bash
python3 src/day13/retry_demos.py
```

### 记录表

| 指标 | 值 |
|------|-----|
| 打印「第 N 次调用」次数 | |
| 最终 result | |
| 若 base_delay 改 1s，总耗时约 | |

### 扩展

复制 `retry_demos.py` 为 `my_401.py`，改为 `status_code=401`，观察调用次数。

---

## Lab 3：is_retryable_error（15 分钟）

```python
from core.exceptions import APIError, ConfigError
from llm.retry import is_retryable_error

cases = [
    ConfigError("x"),
    APIError("a", status_code=429),
    APIError("b", status_code=401),
    APIError("c", status_code=503),
    APIError("d"),
    ValueError("e"),
]
for c in cases:
    print(type(c).__name__, is_retryable_error(c))
```

手填 True/False 列，与 [17_retry速查手册.md](17_retry速查手册.md) 核对。

---

## Lab 4：ResilientLLMClient 端到端（25 分钟）

```bash
NEXUS_LLM_MOCK=1 python3 src/day13/resilient_client_demo.py
```

### 记录表

| 行 | 含义 |
|----|------|
| transport #1 | |
| ⏳ 重试 1/3 | |
| transport #2 | |
| 最终回复 content | |

### 实验 A

`fail_times=5`, `max_attempts=4` → 预期行为？

### 实验 B

`on_retry_log=False` → 输出差异？

---

## Lab 5：RetryPolicy 参数（15 分钟）

```python
from llm.retry import RetryPolicy

p = RetryPolicy(max_attempts=5, base_delay=0.5, backoff_factor=2)
# 手算前 3 次 sleep: 0.5, 1.0, 2.0
```

验证：写迷你循环打印 `min(delay, p.max_delay)` 与 `delay *= p.backoff_factor`。

---

## Lab 6：with_timeout（20 分钟）

```python
import time
from llm.retry import with_timeout
from core.exceptions import APIError

@with_timeout(0.2)
def slow():
    time.sleep(1.0)
    return "ok"

try:
    slow()
except APIError as e:
    print(e)  # 调用超时（>0.2s）
```

### 追问

超时异常会被 `is_retryable_error` 判为可重试吗？

---

## Lab 7：asyncio 预习（15 分钟）

```bash
python3 src/day13/async_demos.py
```

对比：将 `gather` 改为三个顺序 `await`，用 `time.perf_counter()` 测耗时。

---

## Lab 8：pytest（20 分钟）

```bash
python3 -m pytest tests/day13/ -v --tb=short
```

若有失败，查 [10_常见问题与排错指南.md](10_常见问题与排错指南.md)。

---

## Lab 9：与 Day 12 对照（15 分钟）

```bash
NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
NEXUS_LLM_MOCK=1 python3 src/day13/resilient_client_demo.py
```

填写 [18_与Day12客户端对照表.md](18_与Day12客户端对照表.md) 中「你的观察」列。

---

## Lab 10：Day 14 预习（10 分钟）

阅读 [README.md](README.md) Day 14 预告，在笔记写：

1. cli_assistant 用哪个 Client？  
2. 多轮对话维护什么数据结构？  
3. 退出命令预期？

---

## 实验报告模板

```markdown
# Day 13 Lab 报告
- 姓名：
- retry_demos 调用次数：
- resilient_demo 重试次数：
- 401 实验结论：
- pytest 结果：
- 今日最大收获（3 句话）：
```

---

## 完成标准

- [ ] 四个 demo 脚本均可运行  
- [ ] 能解释装饰器顺序  
- [ ] 能区分 429 与 401 策略  
- [ ] pytest day13 全绿  
- [ ] 完成 Day 14 预习笔记

---

*回到索引：[README.md](README.md)*
