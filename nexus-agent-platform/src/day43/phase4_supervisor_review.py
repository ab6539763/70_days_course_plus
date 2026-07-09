"""Phase 4 Supervisor 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "agent/supervisor_config.py — max_delegations / mock_routing",
    "agent/sub_agent.py — faq_worker / rag_worker / intent_worker",
    "agent/supervisor_graph.py — supervisor_route → worker → synthesize",
    "GET/PUT /api/agent/supervisor-config",
    "POST /api/agent/supervisor-preview",
    "POST /api/chat supervisor_mode=true → supervisor_trace + delegated_agents",
]


def main() -> int:
    print("=" * 58)
    print("  Day 43 Supervisor 多 Agent 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
