"""
MCP 协议消息类型 — tools/list 与 tools/call

对齐 Model Context Protocol 工具发现/调用语义（无 mcp SDK 依赖）。

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MCP_METHOD_LIST = "tools/list"
MCP_METHOD_CALL = "tools/call"


@dataclass(frozen=True)
class McpToolDescriptor:
    """MCP tools/list 返回的工具描述"""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class McpJsonRpcRequest:
    """JSON-RPC 风格 MCP 请求"""

    jsonrpc: str = "2.0"
    id: str | int = "1"
    method: str = MCP_METHOD_LIST
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": dict(self.params),
        }


@dataclass
class McpJsonRpcResponse:
    """JSON-RPC 风格 MCP 响应"""

    jsonrpc: str = "2.0"
    id: str | int = "1"
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            payload["error"] = self.error
        else:
            payload["result"] = self.result or {}
        return payload

    @property
    def ok(self) -> bool:
        return self.error is None
