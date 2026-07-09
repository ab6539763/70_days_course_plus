"""
手写 ReAct Agent 演示

运行：PYTHONPATH=src python3 src/day39/react_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.react_agent import ReActAgent
from agent.react_config import ReactConfig
from api.factory import create_orchestrator
from day39.constants import REACT_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 39 手写 ReAct Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    agent = ReActAgent(
        orchestrator.tool_executor,
        config=ReactConfig(enabled=True, max_steps=3),
    )

    for item in REACT_CASES:
        q = item["query"]
        outcome = agent.run(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    tools={list(outcome.tools_used)} steps={len(outcome.steps)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.action:
                print(f"      step{step.step}: {step.action} → {step.observation[:60]}...")

    print("\n  ✅ ReAct 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
