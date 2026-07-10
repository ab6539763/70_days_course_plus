"""
MCP 配置 — 自研 MCP Server 暴露 Nexus 工具链

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class McpConfig:
    """MCP 协议桥接策略"""

    enabled: bool = True
    server_name: str = "nexus-tools"
    expose_external_tools: bool = True
    mock_routing: bool = True
    use_session_history: bool = True
    return_mcp_trace: bool = True
    max_tool_calls: int = 2

    def validate(self) -> None:
        if self.max_tool_calls < 1 or self.max_tool_calls > 4:
            raise ValueError(f"max_tool_calls 须在 1~4，收到 {self.max_tool_calls}")
        if not (self.server_name or "").strip():
            raise ValueError("server_name 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "server_name": self.server_name,
            "expose_external_tools": self.expose_external_tools,
            "mock_routing": self.mock_routing,
            "use_session_history": self.use_session_history,
            "return_mcp_trace": self.return_mcp_trace,
            "max_tool_calls": self.max_tool_calls,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> McpConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            server_name=str(data.get("server_name", "nexus-tools")),
            expose_external_tools=bool(data.get("expose_external_tools", True)),
            mock_routing=bool(data.get("mock_routing", True)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_mcp_trace=bool(data.get("return_mcp_trace", True)),
            max_tool_calls=int(data.get("max_tool_calls", 2)),
        )
