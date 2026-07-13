"""
McpClient — 进程内 MCP 客户端，对接 NexusMcpServer

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from typing import Any

from agent.mcp_protocol import (
    MCP_METHOD_CALL,
    MCP_METHOD_LIST,
    McpJsonRpcRequest,
    McpToolDescriptor,
)
from agent.mcp_server import NexusMcpServer


class McpClient:
    """轻量 MCP 客户端 — list / call 封装"""

    def __init__(self, server: NexusMcpServer) -> None:
        self._server = server

    @property
    def server_name(self) -> str:
        return self._server.server_name

    def list_tools(self) -> list[McpToolDescriptor]:
        resp = self._server.handle(McpJsonRpcRequest(method=MCP_METHOD_LIST))
        if not resp.ok:
            raise RuntimeError(resp.error)
        raw_tools = (resp.result or {}).get("tools") or []
        return [
            McpToolDescriptor(
                name=str(t["name"]),
                description=str(t.get("description", "")),
                input_schema=dict(t.get("inputSchema") or {}),
            )
            for t in raw_tools
        ]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        resp = self._server.handle(
            McpJsonRpcRequest(
                method=MCP_METHOD_CALL,
                params={"name": name, "arguments": dict(arguments or {})},
            )
        )
        if not resp.ok:
            raise RuntimeError(resp.error)
        blocks = (resp.result or {}).get("content") or []
        if not blocks:
            return ""
        return str(blocks[0].get("text", ""))
