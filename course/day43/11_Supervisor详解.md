# Supervisor 详解（Day 43 专题）

## 1. 委派

Supervisor 分析 query → 选择子 Agent → 执行工具 → synthesize 汇总。

## 2. 子 Agent

- `faq_worker` → faq_lookup
- `rag_worker` → rag_search
- `intent_worker` → intent_classify

## 3. 可观测

`supervisor_trace[]` 含 `delegated_agent`；`delegated_agents[]` 汇总委派路径。
