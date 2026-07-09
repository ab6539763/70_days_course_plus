# AgentExecutor 详解（Day 40 专题）

## 1. StructuredTool

`@tool` 装饰器注册函数 → OpenAI function schema → `StructuredTool.run()`

## 2. invoke 循环

```
plan → tool.run → observation → … → Final Answer
```

## 3. 与 ReAct 对齐

`ExecutorStep` 字段与 Day 39 `ReactStep` 一致；`executor_trace` 可对照 `executor_trace`。
