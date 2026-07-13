# Day 43 课件索引

**主题**：Supervisor 多 Agent 委派 — faq_worker / rag_worker / intent_worker
**需求**：ZL-NA-REQ-043
**平台版本**：v0.43.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/supervisor_config.py` | SupervisorConfig — max_delegations |
| `agent/sub_agent.py` | 三个专职子 Agent |
| `agent/supervisor_graph.py` | supervisor_route → worker → synthesize |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/supervisor-config | 配置读写 |
| POST /api/agent/supervisor-preview | 无状态预览，返回 `supervisor_trace` |


`POST /api/chat` + `supervisor_mode: true` → 响应含 `supervisor_trace` + delegated_agents + tools_used。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day43/supervisor_demo.py
python3 src/day43/supervisor_api_demo.py
python3 -m pytest tests/day43/ -v
```

## 关键流程

Day42 让单 Agent 可管控；Day43 让多个专职 Agent 协作委派。

## 验收

`tests/day43/` 17 项全绿；`day43/phase4_supervisor_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day43_course.py
```
