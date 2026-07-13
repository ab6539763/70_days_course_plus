"""
Supervisor 多 Agent 演示

运行：PYTHONPATH=src python3 src/day43/supervisor_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.sub_agent import SUB_AGENTS
from agent.supervisor_config import SupervisorConfig
from agent.supervisor_graph import SupervisorGraph
from api.factory import create_orchestrator
from day43.constants import SUPERVISOR_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 43 Supervisor 多 Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    graph = SupervisorGraph.from_executor(
        orchestrator.tool_executor,
        config=SupervisorConfig(enabled=True),
    )

    print(f"\n  子 Agent: {[s.name for s in SUB_AGENTS]}")
    for item in SUPERVISOR_CASES:
        outcome = graph.invoke(item["query"])
        agent = outcome.delegated_agents[-1] if outcome.delegated_agents else "none"
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if agent == item["expect_agent"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    delegated={list(outcome.delegated_agents)} node_path={list(outcome.node_path)} {flag}")
        print(f"    tools={list(outcome.tools_used)} reply: {outcome.reply[:70]}...")

    print("\n  ✅ Supervisor 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
