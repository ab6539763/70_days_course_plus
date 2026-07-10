# Day 40 课件索引

**主题**：AgentExecutor 框架工具链 — StructuredTool + invoke + intermediate_steps
**需求**：ZL-NA-REQ-040
**平台版本**：v0.40.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/structured_tool.py` | StructuredTool + @tool 装饰器 + OpenAI schema |
| `agent/tool_adapter.py` | ToolRegistry → StructuredTool 适配 |
| `agent/agent_executor.py` | AgentExecutor.invoke 可观测循环 |
| `agent/executor_config.py` | ExecutorConfig — max_iterations |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/executor-config | 配置读写 |
| POST /api/agent/executor-preview | 无状态预览，返回 `executor_trace` |


`POST /api/chat` + `executor_mode: true` → 响应含 `executor_trace` + tools_used。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day40/executor_demo.py
python3 src/day40/executor_api_demo.py
python3 -m pytest tests/day40/ -v
```

## 关键流程

Day39 手写 ReAct 验证思路；Day40 用 StructuredTool 把工具注册框架化。

## 验收

`tests/day40/` 17 项全绿；`day40/phase4_executor_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day40_course.py
```
