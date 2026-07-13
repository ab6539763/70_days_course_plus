"""Phase 4 MCP 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/mcp_config.py — server_name / mock_routing / max_tool_calls",
    "agent/mcp_protocol.py — tools/list + tools/call JSON-RPC",
    "agent/mcp_server.py — NexusMcpServer 暴露 ToolRegistry",
    "agent/mcp_client.py + mcp_bridge.py — MCP → StructuredTool",
    "agent/mcp_runner.py — discover → route → call → answer",
    "GET/PUT /api/agent/mcp-config",
    "POST /api/agent/mcp-list-tools + mcp-preview",
    "POST /api/chat mcp_mode=true → mcp_trace + mcp_tools",
]


def main() -> int:
    print("=" * 58)
    print("  Day 44 MCP 协议与工具生态回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
