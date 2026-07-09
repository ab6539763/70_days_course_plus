"""
RAG Agent StateGraph — planner → tool → answer 三节点编排

复用 Day 40 StructuredTool，将 AgentExecutor 线性循环升级为显式状态图。

需求：ZL-NA-REQ-041
"""

from __future__ import annotations

import re
from typing import Any

from agent.graph_config import GraphConfig
from agent.graph_state import AgentGraphState
from agent.state_graph import END, CompiledStateGraph, GraphRunOutcome, GraphStep, StateGraph
from agent.structured_tool import StructuredTool
from agent.tool_adapter import tool_map, tools_from_executor
from tools.executor import ToolExecutor


class RAGAgentGraph:
    """Nexus RAG Agent 预置状态图"""

    def __init__(
        self,
        tools: list[StructuredTool],
        *,
        config: GraphConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._config = config or GraphConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: GraphConfig | None = None,
    ) -> RAGAgentGraph:
        return cls(tools_from_executor(executor), config=config)

    @property
    def config(self) -> GraphConfig:
        return self._config

    @property
    def compiled(self) -> CompiledStateGraph:
        return self._graph

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> GraphRunOutcome:
        query = (query or "").strip()
        cfg = self._config
        if not query:
            return GraphRunOutcome(
                query="",
                reply="请输入有效问题。",
                steps=(),
                tools_used=(),
                node_path=(),
            )
        if not cfg.enabled:
            return GraphRunOutcome(
                query=query,
                reply="StateGraph 已关闭。",
                steps=(),
                tools_used=(),
                node_path=(),
            )

        state = AgentGraphState(
            query=query,
            history=list(history or []),
        )
        steps: list[GraphStep] = []
        final = self._graph.invoke(
            state,
            max_iterations=cfg.max_iterations,
            step_recorder=steps,
        )
        node_path = tuple(s.node for s in steps)
        return GraphRunOutcome(
            query=query,
            reply=final.reply or "未得到答案。",
            steps=tuple(steps),
            tools_used=tuple(dict.fromkeys(final.tools_used)),
            node_path=node_path,
        )

    def _build_graph(self) -> StateGraph:
        g = StateGraph()
        g.add_node("planner", self._node_planner)
        g.add_node("tool_runner", self._node_tool_runner)
        g.add_node("answer", self._node_answer)
        g.set_entry_point("planner")
        g.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {"tool": "tool_runner", "answer": "answer"},
        )
        g.add_conditional_edges(
            "tool_runner",
            self._route_after_tool,
            {"planner": "planner", "answer": "answer"},
        )
        g.add_edge("answer", END)
        return g

    def _node_planner(self, state: AgentGraphState) -> AgentGraphState:
        state.iteration += 1
        thought, action, action_input, final = self._mock_plan(state)
        if final:
            state.reply = final
            state.done = True
            state.pending_action = None
            state.pending_input = {}
            return state
        state.pending_action = action
        state.pending_input = dict(action_input or {})
        return state

    def _node_tool_runner(self, state: AgentGraphState) -> AgentGraphState:
        action = state.pending_action
        if not action or action not in self._tool_by_name:
            state.reply = "状态图未能执行有效工具。"
            state.done = True
            return state
        observation = self._tool_by_name[action].run(state.pending_input)
        state.last_observation = observation
        if not observation.strip().endswith("失败:"):
            state.tools_used.append(action)
        state.pending_action = None
        state.pending_input = {}
        return state

    def _node_answer(self, state: AgentGraphState) -> AgentGraphState:
        if state.reply:
            state.done = True
            return state
        if state.last_observation:
            state.reply = self._observation_to_answer(state.last_observation, state.query)
        else:
            state.reply = "未在迭代上限内得到答案，请换个问法。"
        state.done = True
        return state

    def _route_after_planner(self, state: AgentGraphState) -> str:
        if state.done:
            return "answer"
        return "tool"

    def _route_after_tool(self, state: AgentGraphState) -> str:
        if state.iteration >= self._config.max_iterations:
            return "answer"
        if state.last_observation:
            return "answer"
        return "planner"

    def _mock_plan(
        self, state: AgentGraphState
    ) -> tuple[str, str | None, dict[str, Any], str | None]:
        if state.last_observation:
            answer = self._observation_to_answer(state.last_observation, state.query)
            hist_note = ""
            if state.history:
                hist_note = f"（结合 {len(state.history)} 条会话记忆）"
            return (
                f"图节点 planner：整理 Final Answer{hist_note}。",
                None,
                {},
                answer,
            )

        query = state.query
        q = query.lower()
        hist_ctx = ""
        if state.history:
            last_user = [h["content"] for h in state.history if h.get("role") == "user"]
            if last_user:
                hist_ctx = f" 上文：{last_user[-1][:40]}"

        if "intent_classify" in self._tool_names and state.iteration == 1 and "总结" in q:
            return (
                f"planner 节点路由 intent_classify。{hist_ctx}",
                "intent_classify",
                {"text": query},
                None,
            )
        if "faq_lookup" in self._tool_names and re.search(
            r"电话|客服|400|热线|联系", q
        ):
            return (
                f"planner 节点路由 faq_lookup。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )
        if "rag_search" in self._tool_names:
            return (
                f"planner 节点路由 rag_search。{hist_ctx}",
                "rag_search",
                {"query": query, "top_k": 3},
                None,
            )
        if "faq_lookup" in self._tool_names:
            return (
                f"planner 回退 faq_lookup。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )
        return ("planner：无可用工具。", None, {}, "暂无法处理该问题。")

    @staticmethod
    def _observation_to_answer(observation: str, query: str) -> str:
        text = observation.strip()
        if text.startswith("[faq_lookup]"):
            body = text.split("]", 1)[-1].strip()
            return body.split("\n")[-1].strip() if "\n" in body else body
        if text.startswith("[rag_search]"):
            body = text.split("]", 1)[-1].strip()
            lines = [ln for ln in body.splitlines() if ln.strip()]
            if lines:
                return f"根据知识库：{lines[0][:200]}"
        if text.startswith("[intent_classify]"):
            return f"根据意图分析：{text.split(']', 1)[-1].strip()}"
        return f"根据工具结果：{text[:300]}"
