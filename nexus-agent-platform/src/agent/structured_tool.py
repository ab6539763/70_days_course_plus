"""
StructuredTool — LangChain 风格 @tool 装饰器与 OpenAI schema 导出

不引入 langchain 依赖，教学对齐 AgentExecutor 工具注册模式。

需求：ZL-NA-REQ-040
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, get_type_hints


ToolFunc = Callable[..., str]


@dataclass
class StructuredTool:
    """可复用工具单元 — 对应 LangChain StructuredTool"""

    name: str
    description: str
    parameters: dict[str, Any]
    func: ToolFunc
    return_direct: bool = False

    def run(self, tool_input: dict[str, Any] | None = None) -> str:
        """执行工具并返回字符串 Observation"""
        payload = dict(tool_input or {})
        try:
            return str(self.func(**payload))
        except TypeError:
            return str(self.func(payload))

    def to_openai_tool(self) -> dict[str, Any]:
        """导出 OpenAI function-calling schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def schema_summary(self) -> str:
        props = self.parameters.get("properties", {})
        keys = ", ".join(props) if props else "无"
        return f"{self.name}({keys}) — {self.description}"


def _json_type(py_type: Any) -> str:
    mapping = {str: "string", int: "integer", float: "number", bool: "boolean"}
    if py_type in mapping:
        return mapping[py_type]
    origin = getattr(py_type, "__origin__", None)
    if origin is list:
        return "array"
    if origin is dict:
        return "object"
    return "string"


def _parameters_from_signature(fn: ToolFunc) -> dict[str, Any]:
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        ann = hints.get(name, str)
        properties[name] = {"type": _json_type(ann), "description": name}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def tool(
    *,
    name: str | None = None,
    description: str | None = None,
    return_direct: bool = False,
) -> Callable[[ToolFunc], StructuredTool]:
    """@tool 装饰器 — 将函数注册为 StructuredTool"""

    def decorator(fn: ToolFunc) -> StructuredTool:
        tool_name = name or fn.__name__
        tool_desc = (description or fn.__doc__ or tool_name).strip().splitlines()[0]
        params = _parameters_from_signature(fn)
        return StructuredTool(
            name=tool_name,
            description=tool_desc,
            parameters=params,
            func=fn,
            return_direct=return_direct,
        )

    return decorator


def tools_to_openai_schema(tools: list[StructuredTool]) -> list[dict[str, Any]]:
    """批量导出工具 schema 供 LLM planner 使用"""
    return [t.to_openai_tool() for t in tools]
