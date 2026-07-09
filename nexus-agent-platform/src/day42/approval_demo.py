"""
人工审批工作流演示

运行：PYTHONPATH=src python3 src/day42/approval_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import GraphConfig
from api.factory import create_orchestrator
from day42.constants import APPROVAL_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 42 人工审批工作流演示")
    print("=" * 60)

    approval_checkpoint_store.clear()
    orchestrator = create_orchestrator()

    # mock 自动审批
    workflow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        graph_config=GraphConfig(max_iterations=3),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )
    for item in APPROVAL_CASES:
        outcome = workflow.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        has_approval = "human_approval" in outcome.node_path
        print(f"\n  Q: {item['query']}")
        print(f"    node_path={list(outcome.node_path)} approval={outcome.approval_status}")
        print(f"    tools={list(outcome.tools_used)} {tool} interrupted={outcome.interrupted}")

    # 中断 + 恢复
    print("\n  --- 中断恢复演示 ---")
    interrupt_flow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = interrupt_flow.invoke("年化收益怎么样")
    print(f"  interrupted={pending.interrupted} checkpoint={pending.checkpoint_id}")
    if pending.checkpoint_id:
        resumed = interrupt_flow.resume(pending.checkpoint_id, approved=True, comment="合规通过")
        print(f"  resumed reply: {resumed.reply[:80]}...")
        print(f"  status={resumed.approval_status}")

    print("\n  ✅ 审批工作流演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
