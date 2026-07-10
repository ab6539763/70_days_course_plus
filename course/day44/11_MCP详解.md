# MCP 详解（Day 44 专题）

## 1. 协议

MCP 用 JSON-RPC 暴露 `tools/list` 与 `tools/call`，与 SubAgent 内嵌工具不同，可对接外部生态。

## 2. 管线

discover → route → call → answer — `mcp_trace[]` 记录每阶段。

## 3. 桥接

`mcp_bridge.structured_tools_from_mcp` 将 MCP 工具转为 StructuredTool，供 Executor/Supervisor 复用。
