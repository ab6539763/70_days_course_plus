# Day 15 token_counter 速查手册

**模块**：`nexus-agent-platform/src/llm/token_counter.py`

---

## 常量

| 名称 | 值 | 含义 |
|------|-----|------|
| `DEFAULT_INPUT_PRICE_PER_M` | 1.0 | 输入单价（元/百万 token） |
| `DEFAULT_OUTPUT_PRICE_PER_M` | 2.0 | 输出单价（元/百万 token） |
| `MESSAGE_OVERHEAD_TOKENS` | 4 | 每条 message 开销 |

---

## 函数

```python
estimate_tokens(text: str) -> int
estimate_message_tokens(message: ChatMessage) -> int
estimate_messages_tokens(messages: list[ChatMessage]) -> int
```

---

## TokenUsage

```python
@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_prompt: int = 0

TokenUsage.from_result(result, estimated_prompt=0)
TokenUsage.from_usage_dict(usage: dict)
usage.format_line()  # tokens: 输入=..., 输出=..., 合计=...
```

---

## TokenCost

```python
@dataclass
class TokenCost:
    input_cost: float
    output_cost: float
    .total  # property
    .format_yuan()
```

---

## TokenCounter

```python
counter = TokenCounter(
    input_price_per_m=1.0,
    output_price_per_m=2.0,
)

counter.estimate_text(text)
counter.estimate_messages(messages)
counter.usage_from_result(result, messages_before_reply)
counter.estimate_cost(usage) -> TokenCost
counter.compare_estimate(usage) -> str
```

---

## TokenSessionTracker

```python
tracker = TokenSessionTracker(counter=None)  # 默认 TokenCounter()

tracker.record_turn(result, messages_before_reply) -> TokenUsage
tracker.last_line() -> str
tracker.summary() -> str
tracker.report() -> str
tracker.stats  # TokenSessionStats
```

---

## TokenSessionStats

```python
stats.turns
stats.prompt_tokens
stats.completion_tokens
stats.total_tokens
stats.total_cost_yuan
stats.history: list[TokenUsage]
stats.record(usage, cost)
stats.summary()
stats.last_usage()
```

---

## CLI 集成速查

```python
ChatAssistant(track_tokens=True)  # 默认
# chat_turn 内: record_turn(result, messages_snapshot)
# /tokens -> token_tracker.report()
```

---

## 常用命令

```bash
export PYTHONPATH=src
python3 src/day15/token_principle_demos.py
python3 src/day15/token_counter_demo.py
NEXUS_LLM_MOCK=1 python3 src/day15/assistant_token_demo.py
python3 -m pytest tests/day15/ -v
```

---

## 费用公式卡片

```
input_cost  = prompt_tokens / 1_000_000 * input_price_per_m
output_cost = completion_tokens / 1_000_000 * output_price_per_m
```

---

## 相关文件

| 文件 | 关系 |
|------|------|
| `llm/response.py` | `ChatCompletionResult` |
| `chat/cli_assistant.py` | `/tokens` 集成 |
| `tests/day15/test_token_counter.py` | 单测 |
