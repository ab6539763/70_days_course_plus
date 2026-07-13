# Day 44 课件索引

**主题**：MCP 协议与工具生态 — 自研 MCP Server — tools/list + tools/call
**需求**：ZL-NA-REQ-044
**平台版本**：v0.44.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/mcp_config.py` | McpConfig — server_name / mock_routing / max_tool_calls |
| `agent/mcp_protocol.py` | JSON-RPC tools/list + tools/call 消息类型 |
| `agent/mcp_server.py` | NexusMcpServer — 暴露 ToolRegistry |
| `agent/mcp_client.py` | McpClient — list/call 封装 |
| `agent/mcp_bridge.py` | MCP → StructuredTool 桥接 |
| `agent/mcp_runner.py` | discover → route → call → answer |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/mcp-config | 配置读写 |
| POST /api/agent/mcp-preview | 无状态预览，返回 `mcp_trace` |
| POST /api/agent/mcp-list-tools | 额外接口 |

`POST /api/chat` + `mcp_mode: true` → 响应含 `mcp_trace` + mcp_tools + tools_used。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day44/mcp_demo.py
python3 src/day44/mcp_api_demo.py
python3 -m pytest tests/day44/ -v
```

## 关键流程

Day43 让 Agent 可协作；Day44 让工具链可扩展 — 用 MCP 协议对接进程外/未来的外部工具。

## 验收

`tests/day44/` 20 项全绿；`day44/phase4_mcp_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day44_course.py
```
