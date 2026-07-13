"""
Dify 工作流对接演示

运行：PYTHONPATH=src python3 src/day45/dify_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.dify_config import DifyConfig
from agent.dify_runner import DifyRunner
from api.factory import create_orchestrator
from day45.constants import DIFY_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 45 Dify 工作流对接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = DifyRunner.from_executor(
        orchestrator.tool_executor,
        config=DifyConfig(enabled=True),
    )

    workflow = runner.export_workflow()
    node_ids = [n.id for n in workflow.nodes]
    print(f"\n  导出 Dify 工作流「{workflow.name}」节点: {node_ids}")

    for item in DIFY_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    tools_used={list(outcome.tools_used)} {flag}")
        print(f"    dify_trace 节点数={len(outcome.dify_trace)}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ Dify 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
