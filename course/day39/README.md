# Day 39 课件索引

**主题**：手写 ReAct Agent — Thought → Action → Observation 可观测工具链
**需求**：ZL-NA-REQ-039
**平台版本**：v0.39.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/react_agent.py` | ReActAgent — Thought/Action/Observation 循环 |
| `agent/react_config.py` | ReactConfig — max_steps / use_session_history |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/react-config | 配置读写 |
| POST /api/agent/react-preview | 无状态预览，返回 `agent_trace` |


`POST /api/chat` + `agent_mode: true` → 响应含 `agent_trace` + tools_used。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day39/react_demo.py
python3 src/day39/react_api_demo.py
python3 -m pytest tests/day39/ -v
```

## 关键流程

Day38 让校验能重试；Day39 让 Agent 能自己选工具。

## 验收

`tests/day39/` 17 项全绿；`day39/phase4_react_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day39_course.py
```
