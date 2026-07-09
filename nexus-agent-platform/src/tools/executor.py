"""
工具执行器 — 校验参数并调用 handler

需求：ZL-NA-REQ-021
"""

from __future__ import annotations

from typing import Any

from tools.tool_registry import ToolDefinition, ToolRegistry, ToolResult


class ToolExecutor:
    """执行 ToolRegistry 中的工具"""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        tool = self.registry.get(name)
        if not tool:
            return ToolResult(name=name, success=False, output="", error=f"未知工具: {name}")

        args = dict(arguments or {})
        try:
            output = _invoke(tool, args)
            return ToolResult(name=name, success=True, output=output)
        except TypeError as exc:
            return ToolResult(name=name, success=False, output="", error=f"参数错误: {exc}")
        except Exception as exc:  # noqa: BLE001 — 工具层统一兜底
            return ToolResult(name=name, success=False, output="", error=str(exc))

    def list_help(self) -> str:
        tools = self.registry.list_tools()
        if not tools:
            return "（无已注册工具）"
        lines = ["已注册工具："]
        for t in tools:
            lines.append(f"  {t.schema_summary()}")
        return "\n".join(lines)


def _invoke(tool: ToolDefinition, args: dict[str, Any]) -> str:
    """按 parameters.required 过滤并调用 handler"""
    props = tool.parameters.get("properties", {})
    required = tool.parameters.get("required", [])
    filtered: dict[str, Any] = {}

    for key in props:
        if key in args:
            filtered[key] = args[key]
    for key in required:
        if key not in filtered:
            # 兼容 query/text 互用
            if key == "query" and "text" in args:
                filtered["query"] = args["text"]
            elif key == "text" and "query" in args:
                filtered["text"] = args["query"]
            else:
                raise TypeError(f"缺少必填参数: {key}")

    return tool.handler(**filtered)
