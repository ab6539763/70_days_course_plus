"""Phase 4 StateGraph 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/state_graph.py — StateGraph 编译与 invoke",
    "agent/graph_state.py — AgentGraphState 共享状态",
    "agent/rag_agent_graph.py — planner → tool_runner → answer",
    "agent/graph_config.py — max_iterations / return_node_trace",
    "GET/PUT /api/agent/graph-config",
    "POST /api/agent/graph-preview",
    "POST /api/chat graph_mode=true → graph_trace + node_path",
]


def main() -> int:
    print("=" * 58)
    print("  Day 41 LangGraph 风格 StateGraph 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
