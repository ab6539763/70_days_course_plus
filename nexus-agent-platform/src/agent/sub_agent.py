"""
SubAgent 定义 — FAQ / RAG / Intent 三个专职子 Agent

需求：ZL-NA-REQ-043
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.structured_tool import StructuredTool
from agent.tool_adapter import tool_map


@dataclass(frozen=True)
class SubAgentSpec:
    """子 Agent 元数据"""

    name: str
    label: str
    tool_name: str
    description: str


SUB_AGENTS: tuple[SubAgentSpec, ...] = (
    SubAgentSpec(
        name="faq_worker",
        label="FAQ 专员",
        tool_name="faq_lookup",
        description="处理标准 FAQ、客服电话类问题",
    ),
    SubAgentSpec(
        name="rag_worker",
        label="知识库专员",
        tool_name="rag_search",
        description="检索企业知识库片段",
    ),
    SubAgentSpec(
        name="intent_worker",
        label="意图分析专员",
        tool_name="intent_classify",
        description="对用户意图分类与总结路由",
    ),
)


def sub_agent_by_name(name: str) -> SubAgentSpec | None:
    for spec in SUB_AGENTS:
        if spec.name == name:
            return spec
    return None


class SubAgentRunner:
    """执行单个子 Agent 的工具调用"""

    def __init__(self, tools: list[StructuredTool]) -> None:
        self._tools = tool_map(tools)

    def run(self, spec: SubAgentSpec, query: str) -> tuple[str, str]:
        tool = self._tools.get(spec.tool_name)
        if not tool:
            return spec.tool_name, f"[{spec.tool_name}] 工具不可用"
        if spec.tool_name == "intent_classify":
            payload: dict[str, Any] = {"text": query}
        elif spec.tool_name == "rag_search":
            payload = {"query": query, "top_k": 3}
        else:
            payload = {"query": query}
        output = tool.run(payload)
        return spec.tool_name, output
