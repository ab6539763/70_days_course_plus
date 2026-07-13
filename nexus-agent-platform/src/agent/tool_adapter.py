"""
ToolRegistry → StructuredTool 适配 — 复用 Day 21 工具链

需求：ZL-NA-REQ-040
"""

from __future__ import annotations

from typing import Any

from agent.structured_tool import StructuredTool
from tools.executor import ToolExecutor


def tools_from_executor(executor: ToolExecutor) -> list[StructuredTool]:
    """将 ToolRegistry 中已注册工具转为 StructuredTool 列表"""
    structured: list[StructuredTool] = []
    for definition in executor.registry.list_tools():

        def _make_handler(tool_name: str):
            def handler(**kwargs: Any) -> str:
                result = executor.execute(tool_name, kwargs)
                return result.summary()

            return handler

        structured.append(
            StructuredTool(
                name=definition.name,
                description=definition.description,
                parameters=definition.parameters,
                func=_make_handler(definition.name),
            )
        )
    return structured


def tool_map(tools: list[StructuredTool]) -> dict[str, StructuredTool]:
    return {t.name: t for t in tools}
