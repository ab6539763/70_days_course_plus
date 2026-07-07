"""
工具定义与注册表 — Function Calling 引擎雏形

将 FAQ、RAG、意图分类等能力封装为可调用工具，供编排层与后续 LLM tool_calls 使用。

需求：ZL-NA-REQ-021
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

ToolHandler = Callable[..., str]


@dataclass
class ToolDefinition:
    """工具元数据与处理函数"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def schema_summary(self) -> str:
        props = self.parameters.get("properties", {})
        keys = ", ".join(props) if props else "无"
        return f"{self.name}({keys}) — {self.description}"


@dataclass
class ToolResult:
    """工具执行结果"""

    name: str
    success: bool
    output: str
    error: str = ""

    def summary(self) -> str:
        if self.success:
            return f"[{self.name}] {self.output}"
        return f"[{self.name}] 失败: {self.error}"


class ToolRegistry:
    """工具注册表"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not tool.name:
            raise ValueError("工具名不能为空")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        return sorted(self._tools)

    def schemas_for_prompt(self) -> str:
        """生成供 system prompt 参考的工具列表"""
        lines = ["可用工具："]
        for t in self.list_tools():
            lines.append(f"  - {t.schema_summary()}")
        return "\n".join(lines)


def build_nexus_tools(
    *,
    faq_matcher=None,
    rag_service=None,
    intent_router=None,
    token_counter=None,
) -> ToolRegistry:
    """构建 NexusAgent 内置工具集"""
    registry = ToolRegistry()

    if faq_matcher is not None:

        def faq_lookup(query: str) -> str:
            match = faq_matcher.match(query)
            if not match:
                return "未匹配到 FAQ"
            return f"{match.summary()}\n{match.entry.answer}"

        registry.register(
            ToolDefinition(
                name="faq_lookup",
                description="相似 FAQ 匹配，适合标准产品/合规/客服问题",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "用户问题"}},
                    "required": ["query"],
                },
                handler=faq_lookup,
            )
        )

    if rag_service is not None:

        def rag_search(query: str, top_k: int = 3) -> str:
            return rag_service.retrieve_context(query, top_k=top_k)

        registry.register(
            ToolDefinition(
                name="rag_search",
                description="从知识库检索相关文档片段",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 3},
                    },
                    "required": ["query"],
                },
                handler=rag_search,
            )
        )

    if intent_router is not None:

        def intent_classify(text: str) -> str:
            return intent_router.classify(text).summary()

        registry.register(
            ToolDefinition(
                name="intent_classify",
                description="意图分类预览，返回模板路由建议",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=intent_classify,
            )
        )

    if token_counter is not None:

        def estimate_tokens(text: str) -> str:
            n = token_counter.estimate_text(text)
            return f"约 {n} tokens"

        registry.register(
            ToolDefinition(
                name="estimate_tokens",
                description="估算文本 token 数量",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=estimate_tokens,
            )
        )

    return registry


def parse_tool_arguments(raw: str) -> dict[str, Any]:
    """解析 /tool 命令的 JSON 参数"""
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        return json.loads(raw)
    # 简写：/tool faq_lookup 投资回报率
    return {"query": raw, "text": raw}
