"""
McpRunner — MCP 工具发现 → 路由 → 调用 → 汇总

需求：ZL-NA-REQ-044
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST
from agent.mcp_server import NexusMcpServer
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class McpStep:
    """MCP 级 trace — 对齐 supervisor_trace 并扩展 mcp_method"""

    step: int
    phase: str
    thought: str
    mcp_method: str | None = None
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "phase": self.phase,
            "thought": self.thought,
            "mcp_method": self.mcp_method,
            "tool": self.tool,
            "arguments": dict(self.arguments or {}),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class McpRunOutcome:
    query: str
    reply: str
    steps: tuple[McpStep, ...]
    tools_used: tuple[str, ...]
    mcp_tools: tuple[str, ...]
    server_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "mcp_tools": list(self.mcp_tools),
            "server_name": self.server_name,
        }


class McpRunner:
    """MCP 协议驱动的工具调用编排"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> None:
        self._config = config or McpConfig()
        self._server = NexusMcpServer(executor, config=self._config)
        self._client = McpClient(self._server)

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: McpConfig | None = None,
    ) -> McpRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> McpConfig:
        return self._config

    def list_tools(self) -> list[str]:
        return [t.name for t in self._client.list_tools()]

    def list_tool_descriptors(self) -> list[dict]:
        return [t.to_dict() for t in self._client.list_tools()]

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> McpRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "MCP 工具桥接已关闭。")

        steps: list[McpStep] = []
        hist_note = ""
        if history and cfg.use_session_history:
            hist_note = f"（结合 {len(history)} 条会话记忆）"

        descriptors = self._client.list_tools()
        mcp_tools = tuple(t.name for t in descriptors)
        steps.append(
            McpStep(
                step=1,
                phase="discover",
                thought=f"通过 MCP tools/list 发现 {len(descriptors)} 个工具{hist_note}。",
                mcp_method=MCP_METHOD_LIST,
            )
        )

        tool_name, arguments, reason = self._route_tool(query, mcp_tools)
        steps.append(
            McpStep(
                step=2,
                phase="route",
                thought=reason,
                tool=tool_name,
                arguments=arguments,
            )
        )

        observation = self._client.call_tool(tool_name, arguments)
        steps.append(
            McpStep(
                step=3,
                phase="call",
                thought=f"经 MCP tools/call 执行 {tool_name}。",
                mcp_method=MCP_METHOD_CALL,
                tool=tool_name,
                arguments=arguments,
                observation=observation,
            )
        )

        reply = self._synthesize(query, observation, tool_name)
        steps.append(
            McpStep(
                step=4,
                phase="answer",
                thought="汇总 MCP 工具 Observation 生成回复。",
                final_answer=reply,
            )
        )

        trace = tuple(steps) if cfg.return_mcp_trace else ()
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=trace,
            tools_used=(tool_name,),
            mcp_tools=mcp_tools,
            server_name=cfg.server_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> McpRunOutcome:
        return McpRunOutcome(
            query=query,
            reply=reply,
            steps=(),
            tools_used=(),
            mcp_tools=(),
            server_name=self._config.server_name,
        )

    def _route_tool(
        self,
        query: str,
        available: tuple[str, ...],
    ) -> tuple[str, dict[str, Any], str]:
        q = query.lower()
        if self._config.mock_routing:
            if any(k in q for k in ("总结", "归纳", "概括", "分类")):
                tool = "intent_classify" if "intent_classify" in available else available[0]
                return tool, {"query": query}, "路由到意图 MCP 工具 intent_classify。"
            if any(k in q for k in ("电话", "客服", "139", "联系")):
                tool = "faq_lookup" if "faq_lookup" in available else available[0]
                return tool, {"query": query}, "路由到 FAQ MCP 工具 faq_lookup。"
            if any(k in q for k in ("收益", "年化", "风险", "理财", "产品")):
                tool = "rag_search" if "rag_search" in available else available[0]
                return tool, {"query": query}, "路由到 RAG MCP 工具 rag_search。"
        if re.search(r"\d{7,}", q):
            tool = "faq_lookup" if "faq_lookup" in available else available[0]
            return tool, {"query": query}, "检测到号码模式，路由 faq_lookup。"
        tool = "rag_search" if "rag_search" in available else available[0]
        return tool, {"query": query}, "默认路由到 rag_search。"

    def _synthesize(self, query: str, observation: str, tool: str) -> str:
        obs = (observation or "").strip()
        if not obs:
            return f"已通过 MCP 调用 {tool}，但未获得有效结果。"
        if len(obs) > 280:
            obs = obs[:277] + "..."
        return f"【MCP:{tool}】{obs}"
