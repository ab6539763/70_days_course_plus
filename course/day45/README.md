# Day 45 课件索引

**主题**：Dify 工作流对接 + Phase 4 周测 — ToolRegistry 导出 Dify DSL，McpStep 映射 Dify 运行 trace
**需求**：ZL-NA-REQ-045
**平台版本**：v0.45.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| DifyConfig | `agent/dify_config.py` | workflow_name / mock_routing / max_nodes |
| Dify DSL | `agent/dify_protocol.py` | DifyNode / DifyEdge / DifyWorkflow / DifyTraceEvent |
| DifyBridge | `agent/dify_bridge.py` | build_dify_workflow + map_steps_to_dify_trace |
| DifyRunner | `agent/dify_runner.py` | 复用 McpRunner 决策/执行，输出 Dify 风格追踪 |
| 周测 | `day45/phase4_quiz.py` | Day 39-44 十题自测 |
| 回顾 | `day45/phase4_review.py` | Phase 4 里程碑串联 |

| API | 说明 |
|-----|------|
| GET/PUT `/api/agent/dify-config` | 配置读写 |
| POST `/api/agent/dify-export` | 导出 Dify 工作流 DSL |
| POST `/api/agent/dify-preview` | 无状态预览，返回 `dify_trace` |

`POST /api/chat` + `dify_mode: true` → 响应含 `dify_trace` + `tools_used`。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day45/dify_demo.py
python3 src/day45/dify_api_demo.py
python3 src/day45/phase4_review.py
python3 src/day45/phase4_quiz.py --scripted
python3 -m pytest tests/day45/ -v
```

## 关键流程

Day44 用 MCP 协议让工具链可跨进程扩展；Day45 把这条工具链**再导出一层**成 Dify 工作流 DSL —— 同一套 `ToolRegistry`，既能被 Nexus 自己的 `McpRunner` 调用，也能被 Dify 这类低代码工作流平台直接编排。

## 验收

`tests/day45/` 27 项全绿；`day45/phase4_quiz.py --scripted` 得分 100/100。

---

## 课件生成

```bash
python3 scripts/generate_day45_course.py
```
