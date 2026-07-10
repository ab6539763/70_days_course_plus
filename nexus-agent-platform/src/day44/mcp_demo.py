"""
MCP 工具桥接演示

运行：PYTHONPATH=src python3 src/day44/mcp_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from api.factory import create_orchestrator
from day44.constants import MCP_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 44 MCP 工具桥接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = McpRunner.from_executor(
        orchestrator.tool_executor,
        config=McpConfig(enabled=True),
    )

    tools = runner.list_tools()
    print(f"\n  MCP Server 工具: {tools}")
    for item in MCP_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    mcp_tools={list(outcome.mcp_tools)} tools_used={list(outcome.tools_used)} {flag}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ MCP 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
