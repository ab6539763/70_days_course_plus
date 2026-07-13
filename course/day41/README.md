# Day 41 课件索引

**主题**：StateGraph 状态图编排 — planner → tool_runner → answer 显式节点图
**需求**：ZL-NA-REQ-041
**平台版本**：v0.41.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/state_graph.py` | StateGraph — add_node/add_edge/compile/invoke |
| `agent/graph_state.py` | AgentGraphState 节点间共享状态 |
| `agent/rag_agent_graph.py` | RAGAgentGraph 三节点预置图 |
| `agent/graph_config.py` | GraphConfig — max_iterations |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/graph-config | 配置读写 |
| POST /api/agent/graph-preview | 无状态预览，返回 `graph_trace` |


`POST /api/chat` + `graph_mode: true` → 响应含 `graph_trace` + node_path + tools_used。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day41/graph_demo.py
python3 src/day41/graph_api_demo.py
python3 -m pytest tests/day41/ -v
```

## 关键流程

Day40 AgentExecutor 是线性 invoke；Day41 用 StateGraph 显式声明节点与边，为后续加审批节点铺路。

## 验收

`tests/day41/` 17 项全绿；`day41/phase4_graph_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day41_course.py
```
