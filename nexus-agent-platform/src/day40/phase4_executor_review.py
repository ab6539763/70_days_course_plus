"""Phase 4 AgentExecutor 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/structured_tool.py — @tool 装饰器 + OpenAI schema",
    "agent/tool_adapter.py — ToolRegistry → StructuredTool",
    "agent/agent_executor.py — invoke + intermediate_steps",
    "agent/executor_config.py — max_iterations / return_intermediate_steps",
    "GET/PUT /api/agent/executor-config",
    "POST /api/agent/executor-preview",
    "POST /api/chat executor_mode=true → executor_trace + tools_used",
]


def main() -> int:
    print("=" * 58)
    print("  Day 40 AgentExecutor 框架工具链回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
