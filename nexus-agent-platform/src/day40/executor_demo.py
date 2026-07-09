"""
AgentExecutor + StructuredTool 演示

运行：PYTHONPATH=src python3 src/day40/executor_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.agent_executor import AgentExecutor
from agent.executor_config import ExecutorConfig
from agent.structured_tool import StructuredTool, tool, tools_to_openai_schema
from api.factory import create_orchestrator
from day40.constants import EXECUTOR_CASES


@tool(name="echo_ping", description="回显测试输入")
def echo_ping(text: str) -> str:
    return f"echo: {text}"


def main() -> int:
    print("=" * 60)
    print("  Day 40 AgentExecutor + StructuredTool 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    executor = AgentExecutor.from_executor(
        orchestrator.tool_executor,
        config=ExecutorConfig(enabled=True, max_iterations=3),
    )

    print(f"\n  已注册 StructuredTool: {len(executor.tools)} 个")
    schemas = tools_to_openai_schema(executor.tools[:3])
    print(f"  OpenAI schema 样例: {schemas[0]['function']['name']}")

    demo_tool = echo_ping
    assert isinstance(demo_tool, StructuredTool)
    print(f"  @tool 装饰器: {demo_tool.run({'text': 'hello'})}")

    for item in EXECUTOR_CASES:
        q = item["query"]
        outcome = executor.invoke(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    tools={list(outcome.tools_used)} steps={len(outcome.steps)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.action:
                obs = (step.observation or "")[:60]
                print(f"      step{step.step}: {step.action} → {obs}...")

    print("\n  ✅ AgentExecutor 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
