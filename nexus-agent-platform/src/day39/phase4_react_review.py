"""Phase 4 ReAct 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/react_agent.py — Thought/Action/Observation 可观测循环",
    "agent/react_config.py — max_steps / use_session_history",
    "GET/PUT /api/agent/react-config",
    "POST /api/agent/react-preview",
    "POST /api/chat agent_mode=true → agent_trace + tools_used",
]


def main() -> int:
    print("=" * 58)
    print("  Day 39 手写 ReAct Agent 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
