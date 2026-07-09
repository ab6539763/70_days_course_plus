"""
StateGraph RAG Agent 演示

运行：PYTHONPATH=src python3 src/day41/graph_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.graph_config import GraphConfig
from agent.rag_agent_graph import RAGAgentGraph
from agent.state_graph import StateGraph
from api.factory import create_orchestrator
from day41.constants import GRAPH_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 41 StateGraph RAG Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    graph = RAGAgentGraph.from_executor(
        orchestrator.tool_executor,
        config=GraphConfig(enabled=True, max_iterations=3),
    )

    print(f"\n  编译图节点: planner → tool_runner → answer")
    print(f"  StateGraph API: add_node / add_edge / add_conditional_edges / compile")

    for item in GRAPH_CASES:
        q = item["query"]
        outcome = graph.invoke(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    node_path={list(outcome.node_path)} tools={list(outcome.tools_used)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.node:
                print(f"      step{step.step} [{step.node}]: {step.thought[:50]}...")

    print("\n  ✅ StateGraph 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
