# ReAct 详解（Day 39 专题）

## 1. 循环

```
Thought → Action → Observation → … → Final Answer
```

## 2. 工具

复用 Day 21 `ToolRegistry`：`faq_lookup`、`rag_search`、`intent_classify`

## 3. 可观测

`agent_trace[]` 每步含 thought/action/observation；`tools_used[]` 汇总。
