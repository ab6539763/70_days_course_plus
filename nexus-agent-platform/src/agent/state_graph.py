"""
StateGraph — LangGraph 兼容的状态机编排引擎（无 langgraph 依赖）

需求：ZL-NA-REQ-041
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agent.graph_state import AgentGraphState

NodeFn = Callable[[AgentGraphState], AgentGraphState]
RouterFn = Callable[[AgentGraphState], str]

END = "__end__"


@dataclass(frozen=True)
class GraphStep:
    """节点级 trace — 与 ReAct / Executor step 字段对齐"""

    step: int
    node: str
    thought: str
    action: str | None = None
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "node": self.node,
            "thought": self.thought,
            "action": self.action,
            "action_input": dict(self.action_input),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class GraphRunOutcome:
    query: str
    reply: str
    steps: tuple[GraphStep, ...]
    tools_used: tuple[str, ...]
    node_path: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "node_path": list(self.node_path),
        }


class StateGraph:
    """可编译状态图 — add_node / add_edge / add_conditional_edges"""

    def __init__(self, state_type: type = AgentGraphState) -> None:
        self._state_type = state_type
        self._nodes: dict[str, NodeFn] = {}
        self._edges: dict[str, str] = {}
        self._conditional: dict[str, tuple[RouterFn, dict[str, str]]] = {}
        self._entry: str | None = None

    def add_node(self, name: str, fn: NodeFn) -> StateGraph:
        self._nodes[name] = fn
        return self

    def set_entry_point(self, name: str) -> StateGraph:
        self._entry = name
        return self

    def add_edge(self, start: str, end: str) -> StateGraph:
        self._edges[start] = end
        return self

    def add_conditional_edges(
        self,
        start: str,
        router: RouterFn,
        mapping: dict[str, str],
    ) -> StateGraph:
        self._conditional[start] = (router, mapping)
        return self

    def compile(self) -> CompiledStateGraph:
        if not self._entry:
            raise ValueError("StateGraph 缺少 entry point")
        return CompiledStateGraph(
            entry=self._entry,
            nodes=dict(self._nodes),
            edges=dict(self._edges),
            conditional=dict(self._conditional),
        )


class CompiledStateGraph:
    """编译后的图 — invoke 遍历节点直到 END"""

    def __init__(
        self,
        *,
        entry: str,
        nodes: dict[str, NodeFn],
        edges: dict[str, str],
        conditional: dict[str, tuple[RouterFn, dict[str, str]]],
    ) -> None:
        self._entry = entry
        self._nodes = nodes
        self._edges = edges
        self._conditional = conditional

    def invoke(
        self,
        state: AgentGraphState,
        *,
        max_iterations: int = 8,
        step_recorder: list[GraphStep] | None = None,
    ) -> AgentGraphState:
        current = state
        node_path: list[str] = []
        steps = step_recorder if step_recorder is not None else []
        step_idx = len(steps)
        guard = 0

        node = self._entry
        while node != END and guard < max_iterations * 4:
            guard += 1
            if node not in self._nodes:
                break
            node_path.append(node)
            before = current.to_dict()
            current = self._nodes[node](current)
            step_idx += 1
            steps.append(
                GraphStep(
                    step=step_idx,
                    node=node,
                    thought=f"节点 {node} 执行完成",
                    action=before.get("pending_action"),
                    action_input=dict(before.get("pending_input") or {}),
                    observation=current.last_observation,
                    final_answer=current.reply if current.done else None,
                )
            )
            if current.done:
                break
            node = self._resolve_next(node, current)
        return current

    def _resolve_next(self, node: str, state: AgentGraphState) -> str:
        if node in self._conditional:
            router, mapping = self._conditional[node]
            key = router(state)
            return mapping.get(key, END)
        return self._edges.get(node, END)
