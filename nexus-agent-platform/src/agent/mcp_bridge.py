"""
MCP → StructuredTool 桥接 — 让 Supervisor/Executor 可消费外部 MCP 工具

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from typing import Any

from agent.mcp_client import McpClient
from agent.structured_tool import StructuredTool


def structured_tools_from_mcp(client: McpClient) -> list[StructuredTool]:
    """将 MCP tools/list 结果转为 StructuredTool 列表"""
    structured: list[StructuredTool] = []
    for descriptor in client.list_tools():

        def _make_handler(tool_name: str, mcp: McpClient):
            def handler(**kwargs: Any) -> str:
                return mcp.call_tool(tool_name, kwargs)

            return handler

        structured.append(
            StructuredTool(
                name=descriptor.name,
                description=descriptor.description,
                parameters=descriptor.input_schema,
                func=_make_handler(descriptor.name, client),
            )
        )
    return structured
