"""
NexusMcpServer — 进程内自研 MCP Server，暴露 ToolRegistry 工具

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from typing import Any

from agent.mcp_config import McpConfig
from agent.mcp_protocol import (
    MCP_METHOD_CALL,
    MCP_METHOD_LIST,
    McpJsonRpcRequest,
    McpJsonRpcResponse,
    McpToolDescriptor,
)
from tools.executor import ToolExecutor


class NexusMcpServer:
    """将 Nexus ToolExecutor 以 MCP tools/list + tools/call 语义对外暴露"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or McpConfig()
        self._tool_names = set(self._executor.registry.list_names())

    @property
    def config(self) -> McpConfig:
        return self._config

    @property
    def server_name(self) -> str:
        return self._config.server_name

    def list_tools(self) -> list[McpToolDescriptor]:
        """tools/list — 导出已注册工具 schema"""
        tools: list[McpToolDescriptor] = []
        for definition in self._executor.registry.list_tools():
            tools.append(
                McpToolDescriptor(
                    name=definition.name,
                    description=definition.description,
                    input_schema=definition.parameters,
                )
            )
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        """tools/call — 执行单个工具并返回文本结果"""
        if name not in self._tool_names:
            raise ValueError(f"未知 MCP 工具: {name}")
        result = self._executor.execute(name, arguments or {})
        return result.summary()

    def handle(self, request: McpJsonRpcRequest | dict[str, Any]) -> McpJsonRpcResponse:
        """处理 JSON-RPC 请求并返回响应"""
        if isinstance(request, dict):
            req = McpJsonRpcRequest(
                jsonrpc=str(request.get("jsonrpc", "2.0")),
                id=request.get("id", "1"),
                method=str(request.get("method", "")),
                params=dict(request.get("params") or {}),
            )
        else:
            req = request

        if not self._config.enabled:
            return McpJsonRpcResponse(
                id=req.id,
                error={"code": -32000, "message": "MCP Server 已关闭"},
            )

        try:
            if req.method == MCP_METHOD_LIST:
                tools = [t.to_dict() for t in self.list_tools()]
                return McpJsonRpcResponse(
                    id=req.id,
                    result={"tools": tools, "server": self.server_name},
                )
            if req.method == MCP_METHOD_CALL:
                params = req.params
                name = str(params.get("name", ""))
                arguments = dict(params.get("arguments") or {})
                content = self.call_tool(name, arguments)
                return McpJsonRpcResponse(
                    id=req.id,
                    result={
                        "content": [{"type": "text", "text": content}],
                        "isError": False,
                    },
                )
            return McpJsonRpcResponse(
                id=req.id,
                error={"code": -32601, "message": f"未知方法: {req.method}"},
            )
        except ValueError as exc:
            return McpJsonRpcResponse(
                id=req.id,
                error={"code": -32602, "message": str(exc)},
            )
