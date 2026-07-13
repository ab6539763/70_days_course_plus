"""
ApprovalWorkflowGraph — planner → tool → human_approval → answer

在 Day 41 StateGraph 上增加人工审批节点与中断恢复。

需求：ZL-NA-REQ-042
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.graph_config import GraphConfig
from agent.graph_state import AgentGraphState
from agent.state_graph import END, GraphStep, StateGraph
from agent.structured_tool import StructuredTool
from agent.tool_adapter import tool_map, tools_from_executor
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class ApprovalGraphOutcome:
    query: str
    reply: str
    steps: tuple[GraphStep, ...]
    tools_used: tuple[str, ...]
    node_path: tuple[str, ...]
    interrupted: bool = False
    checkpoint_id: str | None = None
    approval_status: str = "skipped"
    approval: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "node_path": list(self.node_path),
            "interrupted": self.interrupted,
            "checkpoint_id": self.checkpoint_id,
            "approval_status": self.approval_status,
            "approval": dict(self.approval),
        }


class ApprovalWorkflowGraph:
    """带人工审批卡点的 RAG Agent 状态图"""

    def __init__(
        self,
        tools: list[StructuredTool],
        *,
        graph_config: GraphConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or GraphConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: GraphConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> GraphConfig:
        return self._graph_config

    @property
    def approval_config(self) -> ApprovalConfig:
        return self._approval_config

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> ApprovalGraphOutcome:
        query = (query or "").strip()
        gcfg = self._graph_config
        acfg = self._approval_config
        if not query:
            return self._outcome("", "请输入有效问题。", [], AgentGraphState())
        if not gcfg.enabled:
            return self._outcome(query, "StateGraph 已关闭。", [], AgentGraphState())
        if not acfg.enabled:
            return self._outcome(query, "人工审批工作流已关闭。", [], AgentGraphState())

        state = AgentGraphState(query=query, history=list(history or []))
        steps: list[GraphStep] = []
        final = self._graph.invoke(
            state,
            max_iterations=gcfg.max_iterations,
            step_recorder=steps,
        )
        return self._finalize(query, final, steps)

    def resume(
        self,
        checkpoint_id: str,
        *,
        approved: bool,
        comment: str = "",
    ) -> ApprovalGraphOutcome:
        cp = approval_checkpoint_store.get(checkpoint_id)
        if cp is None:
            return ApprovalGraphOutcome(
                query="",
                reply="检查点不存在或已过期。",
                steps=(),
                tools_used=(),
                node_path=(),
                approval_status="error",
                approval={"error": "checkpoint_not_found"},
            )

        state = AgentGraphState.from_dict(cp.state.to_dict())
        steps = [
            GraphStep(
                step=int(s["step"]),
                node=str(s["node"]),
                thought=str(s.get("thought", "")),
                action=s.get("action"),
                action_input=dict(s.get("action_input") or {}),
                observation=s.get("observation"),
                final_answer=s.get("final_answer"),
            )
            for s in cp.steps
        ]

        acfg = self._approval_config
        state.interrupted = False
        if approved:
            state.approval_status = "approved"
            state.approver_note = comment or f"已由 {acfg.reviewer_label} 批准"
            final = self._graph.invoke(
                state,
                max_iterations=self._graph_config.max_iterations,
                step_recorder=steps,
                start_at="answer",
            )
        else:
            state.approval_status = "rejected"
            state.approver_note = comment or acfg.reject_message
            state.reply = acfg.reject_message
            state.done = True
            final = state
            steps.append(
                GraphStep(
                    step=len(steps) + 1,
                    node="human_approval",
                    thought="审批驳回，流程终止。",
                    final_answer=state.reply,
                )
            )

        approval_checkpoint_store.delete(checkpoint_id)
        return self._finalize(state.query, final, steps)

    def _finalize(
        self,
        query: str,
        state: AgentGraphState,
        steps: list[GraphStep],
    ) -> ApprovalGraphOutcome:
        if state.interrupted and state.checkpoint_id:
            cp = approval_checkpoint_store.save(
                state,
                steps=[s.to_dict() for s in steps],
                node_path=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                node_path=tuple(s.node for s in steps),
                interrupted=True,
                checkpoint_id=cp.checkpoint_id,
                approval_status="pending",
                approval={
                    "status": "pending",
                    "checkpoint_id": cp.checkpoint_id,
                    "pending_tool": state.pending_tool,
                    "reviewer_label": self._approval_config.reviewer_label,
                },
            )

        return ApprovalGraphOutcome(
            query=query,
            reply=state.reply or "未得到答案。",
            steps=tuple(steps),
            tools_used=tuple(dict.fromkeys(state.tools_used)),
            node_path=tuple(s.node for s in steps),
            interrupted=False,
            approval_status=state.approval_status,
            approval={
                "status": state.approval_status,
                "reviewer_label": self._approval_config.reviewer_label,
                "note": state.approver_note,
            },
        )

    def _outcome(
        self,
        query: str,
        reply: str,
        steps: list[GraphStep],
        state: AgentGraphState,
    ) -> ApprovalGraphOutcome:
        return ApprovalGraphOutcome(
            query=query,
            reply=reply,
            steps=tuple(steps),
            tools_used=tuple(state.tools_used),
            node_path=tuple(s.node for s in steps),
            approval_status=state.approval_status,
        )

    def _build_graph(self) -> StateGraph:
        g = StateGraph()
        g.add_node("planner", self._node_planner)
        g.add_node("tool_runner", self._node_tool_runner)
        g.add_node("human_approval", self._node_human_approval)
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
            {"approval": "human_approval", "planner": "planner", "answer": "answer"},
        )
        g.add_conditional_edges(
            "human_approval",
            self._route_after_approval,
            {"answer": "answer", "interrupt": END},
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
        state.pending_tool = action
        if not observation.strip().endswith("失败:"):
            state.tools_used.append(action)
        state.pending_action = None
        state.pending_input = {}
        return state

    def _node_human_approval(self, state: AgentGraphState) -> AgentGraphState:
        acfg = self._approval_config
        if acfg.mock_auto_approve:
            state.approval_status = "approved"
            state.approver_note = f"mock 自动批准（{acfg.reviewer_label}）"
            state.interrupted = False
            return state

        import uuid

        state.approval_status = "pending"
        state.interrupted = True
        state.checkpoint_id = str(uuid.uuid4())
        state.done = False
        return state

    def _node_answer(self, state: AgentGraphState) -> AgentGraphState:
        if state.approval_status == "rejected":
            state.done = True
            return state
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
        if self._needs_approval(state):
            return "approval"
        if state.iteration >= self._graph_config.max_iterations:
            return "answer"
        if state.last_observation:
            return "answer"
        return "planner"

    def _route_after_approval(self, state: AgentGraphState) -> str:
        if state.interrupted:
            return "interrupt"
        return "answer"

    def _needs_approval(self, state: AgentGraphState) -> bool:
        acfg = self._approval_config
        if not acfg.enabled or not acfg.require_rag_approval:
            return False
        if state.approval_status in ("approved", "rejected"):
            return False
        return state.pending_tool == "rag_search" or (
            state.tools_used and state.tools_used[-1] == "rag_search"
        )

    def _mock_plan(
        self, state: AgentGraphState
    ) -> tuple[str, str | None, dict[str, Any], str | None]:
        if state.last_observation and state.approval_status == "approved":
            answer = self._observation_to_answer(state.last_observation, state.query)
            hist_note = ""
            if state.history:
                hist_note = f"（结合 {len(state.history)} 条会话记忆）"
            return (
                f"审批已通过，planner 整理 Final Answer{hist_note}。",
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
                f"planner 节点路由 rag_search（需审批）。{hist_ctx}",
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
