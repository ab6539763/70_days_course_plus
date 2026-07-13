# Day 42 精读：approval_workflow 与人工审批管线

**需求**：ZL-NA-REQ-042 | **学时**：120 min

---

## 一、approval_workflow_graph.py 全文

```python
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
from agent.graph_config import ApprovalConfig
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
    checkpoint_id: tuple[str, ...]
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
            "checkpoint_id": list(self.checkpoint_id),
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
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or ApprovalConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> ApprovalConfig:
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
                checkpoint_id=(),
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
                checkpoint_id=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
```


---

## 二、行级注释：QueryRouter 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rewrite(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、RuleBasedQueryRouter.route（L33–L68）

```python
"""
人工审批配置 — RAG 工具结果需审批后方可输出

需求：ZL-NA-REQ-042
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApprovalConfig:
    """LangGraph 人工审批卡点策略"""

    enabled: bool = True
    require_rag_approval: bool = True
    mock_auto_approve: bool = True
    reviewer_label: str = "值班审核员"
    reject_message: str = "审批未通过，请补充材料后重试。"

    def validate(self) -> None:
        label = (self.reviewer_label or "").strip()
        if not label:
            raise ValueError("reviewer_label 不能为空")
        if len(label) > 32:
            raise ValueError("reviewer_label 过长")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "require_rag_approval": self.require_rag_approval,
            "mock_auto_approve": self.mock_auto_approve,
            "reviewer_label": self.reviewer_label,
            "reject_message": self.reject_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ApprovalConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            require_rag_approval=bool(data.get("require_rag_approval", True)),
            mock_auto_approve=bool(data.get("mock_auto_approve", True)),
            reviewer_label=str(data.get("reviewer_label", "值班审核员")),
            reject_message=str(
                data.get("reject_message", "审批未通过，请补充材料后重试。")
            ),
        )
```


| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `rewrite`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、rewrite 全文

```python
class ApprovalWorkflowGraph:
    """带人工审批卡点的 RAG Agent 状态图"""

    def __init__(
        self,
        tools: list[StructuredTool],
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or ApprovalConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> ApprovalConfig:
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
                checkpoint_id=(),
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
                checkpoint_id=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
            approval_status=state.approval_status,
        )
```


| 行 | 讲解 |
|----|------|
| 子串分支 | `q in t` → 1.0，电话/SKU 金路径 |
| coverage | matched tokens / query tokens |
| bigram_bonus | 连续二字共现比例 |
| length_penalty | 抑制长文噪声 |
| clamp | [0, 1] 便于 UI 展示 sim=% |

---

## 五、_bigram_overlap

```python
class ApprovalWorkflowGraph:
    """带人工审批卡点的 RAG Agent 状态图"""

    def __init__(
        self,
        tools: list[StructuredTool],
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or ApprovalConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> ApprovalConfig:
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
                checkpoint_id=(),
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
                checkpoint_id=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
            approval_status=state.approval_status,
        )
```


中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、context.py 全文

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 七、search 主流程

```python
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
```


| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rewrite 开销 |
| pool 计算 | `max(max_citations, top_k)` |
| candidates | inner hybrid 宽召回 |
| rewrite 调用 | MockCrossEncoder 改写截断 |

---

## 八、citation_config.py 全文

```python
"""
人工审批配置 — RAG 工具结果需审批后方可输出

需求：ZL-NA-REQ-042
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApprovalConfig:
    """LangGraph 人工审批卡点策略"""

    enabled: bool = True
    require_rag_approval: bool = True
    mock_auto_approve: bool = True
    reviewer_label: str = "值班审核员"
    reject_message: str = "审批未通过，请补充材料后重试。"

    def validate(self) -> None:
        label = (self.reviewer_label or "").strip()
        if not label:
            raise ValueError("reviewer_label 不能为空")
        if len(label) > 32:
            raise ValueError("reviewer_label 过长")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "require_rag_approval": self.require_rag_approval,
            "mock_auto_approve": self.mock_auto_approve,
            "reviewer_label": self.reviewer_label,
            "reject_message": self.reject_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ApprovalConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            require_rag_approval=bool(data.get("require_rag_approval", True)),
            mock_auto_approve=bool(data.get("mock_auto_approve", True)),
            reviewer_label=str(data.get("reviewer_label", "值班审核员")),
            reject_message=str(
                data.get("reject_message", "审批未通过，请补充材料后重试。")
            ),
        )
```


`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

```python
def get_approval_config(self) -> ApprovalConfig:
        return ApprovalConfig.from_dict(self.approval_config.to_dict())

    def set_approval_config(self, config: ApprovalConfig) -> ApprovalConfig:
        config.validate()
        self.approval_config = ApprovalConfig.from_dict(config.to_dict())
        return self.approval_config

    def get_supervisor_config(self) -> SupervisorConfig:
        return SupervisorConfig.from_dict(self.supervisor_config.to_dict())

    def set_supervisor_config(self, config: SupervisorConfig) -> SupervisorConfig:
        config.validate()
        self.supervisor_config = SupervisorConfig.from_dict(config.to_dict())
        return self.supervisor_config

    def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config

    def get_dify_config(self) -> DifyConfig:
        return DifyConfig.from_dict(self.dify_config.to_dict())

    def set_dify_config(self, config: DifyConfig) -> DifyConfig:
        config.validate()
        self.dify_config = DifyConfig.from_dict(config.to_dict())
        return self.dify_config
```


`RAGContextService(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_query_router.py

```python
"""Day 42 ApprovalWorkflowGraph 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import ApprovalConfig
from api.factory import create_orchestrator


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def workflow():
    orch = create_orchestrator()
    return ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        graph_config=ApprovalConfig(max_iterations=4),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )


def test_approval_config_validate():
    ApprovalConfig().validate()
    with pytest.raises(ValueError):
        ApprovalConfig(reviewer_label="").validate()


def test_faq_skips_approval_node(workflow):
    outcome = workflow.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "human_approval" not in outcome.checkpoint_id
    assert outcome.approval_status in ("skipped", "approved")


def test_rag_with_mock_auto_approve(workflow):
    outcome = workflow.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert "human_approval" in outcome.checkpoint_id
    assert outcome.approval_status == "approved"
    assert not outcome.interrupted


def test_interrupt_and_resume_approve():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    assert pending.interrupted
    assert pending.checkpoint_id
    assert pending.approval_status == "pending"

    resumed = flow.resume(pending.checkpoint_id, approved=True, comment="OK")
    assert resumed.approval_status == "approved"
    assert resumed.reply
    assert not resumed.interrupted


def test_interrupt_and_resume_reject():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    resumed = flow.resume(pending.checkpoint_id, approved=False)
    assert resumed.approval_status == "rejected"
    assert "未通过" in resumed.reply or "审批" in resumed.reply


def test_approval_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_approval_config(
        ApprovalConfig(mock_auto_approve=False, reviewer_label="风控专员")
    )
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_approval_config()
    assert cfg.mock_auto_approve is False
    assert cfg.reviewer_label == "风控专员"


def test_resume_unknown_checkpoint():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(orch.tool_executor)
    outcome = flow.resume("missing-id", approved=True)
    assert outcome.approval_status == "error"
```


| 测试 | 要点 |
|------|------|
| test_RuleBasedQueryRouter.route_from_results_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_citation_preview_with_rewrite | 业务号码 |
| test_context_disabled | 降级路径 |
| test_fetch_citations_with_hits_accessible | inner 类型 |
| test_knowledge_store_persists_citation_config | 持久化 |

---

## 十一、API 测试 test_route_api.py

```python
"""Day 42 Approval API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from agent.approval_checkpoint import approval_checkpoint_store
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_approval_config_default(client):
    data = client.get("/api/agent/approval-config").json()
    assert data["enabled"] is True
    assert data["mock_auto_approve"] is True


def test_put_approval_config(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员A",
            "reject_message": "驳回",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mock_auto_approve"] is False


def test_approval_preview_rag_auto(client):
    resp = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "human_approval" in data["checkpoint_id"]
    assert data["approval_status"] == "approved"


def test_approval_interrupt_resume(client):
    client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员",
            "reject_message": "审批未通过",
        },
    )
    preview = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["interrupted"] is True
    cid = body["checkpoint_id"]
    assert cid

    resume = client.post(
        "/api/agent/approval-resume",
        json={"checkpoint_id": cid, "approved": True, "comment": "通过"},
    )
    assert resume.status_code == 200
    assert resume.json()["approval_status"] == "approved"


def test_status_includes_approval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["approval_config"]["enabled"] is True


def test_chat_approval_mode(client):
    resp = client.post(
        "/api/chat",
        json={"message": "年化收益", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert body.get("approval")
    assert body.get("graph_trace")


def test_chat_approval_mode_faq(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert "faq_lookup" in (body.get("tools_used") or [])


def test_invalid_reviewer_label_422(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": True,
            "reviewer_label": "",
            "reject_message": "x",
        },
    )
    assert resp.status_code == 422
```


`test_health_version` 锁版本 `v0.42.0`；`test_chat_includes_citations` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rewrite 后前 3 的 rewrite  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json citation_config  

---

## 十三、自检

1. 手绘三阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rewrite 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 口语命中 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day33 衔接

HybridRetriever 仍是 inner；关 rewrite 即回 Day33 行为。retrieval_config 与 citation_config 正交。

---

## 十六、knowledge_store rewrite 方法

```python
def get_approval_config(self) -> ApprovalConfig:
        return ApprovalConfig.from_dict(self.approval_config.to_dict())

    def set_approval_config(self, config: ApprovalConfig) -> ApprovalConfig:
        config.validate()
        self.approval_config = ApprovalConfig.from_dict(config.to_dict())
        return self.approval_config

    def get_supervisor_config(self) -> SupervisorConfig:
        return SupervisorConfig.from_dict(self.supervisor_config.to_dict())

    def set_supervisor_config(self, config: SupervisorConfig) -> SupervisorConfig:
        config.validate()
        self.supervisor_config = SupervisorConfig.from_dict(config.to_dict())
        return self.supervisor_config

    def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config

    def get_dify_config(self) -> DifyConfig:
        return DifyConfig.from_dict(self.dify_config.to_dict())

    def set_dify_config(self, config: DifyConfig) -> DifyConfig:
        config.validate()
        self.dify_config = DifyConfig.from_dict(config.to_dict())
        return self.dify_config
```


`set_citation_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rewrite 是什么。  
2. 1 分钟对比召回与改写。  
3. 白板画 RAGContextService.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q citations 与 context 重复吗？** 可优化；当前同步教学实现。  
**Q matched_tokens 来源？** 来自 RetrievalResult，展示在 Citation 中。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RuleBasedQueryRouter.route` 与 `RoutingRetriever.search`，并映射到 ZL-NA-REQ-042 的 FR-001–FR-003。

---

## 二十一、approval_workflow 完整源码（重复嵌入便于打印）

```python
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
from agent.graph_config import ApprovalConfig
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
    checkpoint_id: tuple[str, ...]
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
            "checkpoint_id": list(self.checkpoint_id),
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
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or ApprovalConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> ApprovalConfig:
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
                checkpoint_id=(),
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
                checkpoint_id=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
```


---

## 二十二、自适应路由伪代码

```
function FETCH_CITATIONS(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(max_citations, top_k)
    C = INNER(q, P)          # HybridRetriever
    return build_citation_bundle(q, C)
```

---

## 二十三、ROUTE_QUERIES 业务解读

| query | 业务意图 | citation 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_citation_config_validate | FR-004 |
| test_RuleBasedQueryRouter.route_from_results_candidates | FR-002 |
| test_context_enabled | FR-003 |
| test_citation_preview_with_rewrite | AC-03 |
| test_knowledge_store_persists_citation_config | FR-005 |
| test_health_version | FR-008 |
| test_put_citation_config_disable | AC-02 |
| test_chat_includes_citations | AC-05 |

---

## 二十五、knowledge API 节选（citation 上下文）

```python
"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-035 / ZL-NA-REQ-036 / ZL-NA-REQ-037 / ZL-NA-REQ-038
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    CitationConfigRequest,
    CitationConfigResponse,
    CitationPreviewRequest,
    CitationPreviewResponse,
    ExpansionConfigRequest,
    ExpansionConfigResponse,
    ExpansionPreviewRequest,
    ExpansionPreviewResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
    RerankConfigRequest,
    RerankConfigResponse,
    RewriteConfigRequest,
    RewriteConfigResponse,
    RewritePreviewRequest,
    RewritePreviewResponse,
    RouteConfigRequest,
    RouteConfigResponse,
    RoutePreviewRequest,
    RoutePreviewResponse,
    ValidationConfigRequest,
    ValidationConfigResponse,
    ValidationPreviewRequest,
    ValidationPreviewResponse,
    ValidationRetryPreviewRequest,
    ValidationRetryPreviewResponse,
    RetrievalConfigRequest,
    RetrievalConfigResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import CitationConfig
from rag.expansion_config import ExpansionConfig
from rag.query_expander import build_expander
from rag.query_rewriter import RuleBasedQueryRewriter
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import RouteConfig
from rag.validation_config import ValidationConfig
from rag.rerank_config import RerankConfig
from rag.rewrite_config import RewriteConfig
from rag.retrieval_config import RetrievalConfig
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
def get_retrieval_config() -> RetrievalConfigResponse:
    """返回当前检索模式（vector / keyword / hybrid）与融合参数"""
    cfg = get_knowledge_store().get_retrieval_config()
    return RetrievalConfigResponse(**cfg.to_dict())


@router.put("/retrieval-config", response_model=RetrievalConfigResponse)
def update_retrieval_config(body: RetrievalConfigRequest) -> RetrievalConfigResponse:
    """更新检索策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RetrievalConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_retrieval_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RetrievalConfigResponse(**cfg.to_dict())


@router.get("/rerank-config", response_model=RerankConfigResponse)
def get_rerank_config() -> RerankConfigResponse:
    """返回 rerank 开关、候选池大小与模型标识"""
    cfg = get_knowledge_store().get_rerank_config()
    return RerankConfigResponse(**cfg.to_dict())


@router.put("/rerank-config", response_model=RerankConfigResponse)
def update_rerank_config(body: RerankConfigRequest) -> RerankConfigResponse:
    """更新 rerank 策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RerankConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rerank_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RerankConfigResponse(**cfg.to_dict())


@router.get("/rewrite-config", response_model=RewriteConfigResponse)
def get_rewrite_config() -> RewriteConfigResponse:
    """返回查询改写开关与规则模式"""
    cfg = get_knowledge_store().get_rewrite_config()
    return RewriteConfigResponse(**cfg.to_dict())


@router.put("/rewrite-config", response_model=RewriteConfigResponse)
def update_rewrite_config(body: RewriteConfigRequest) -> RewriteConfigResponse:
    """更新查询改写策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RewriteConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rewrite_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RewriteConfigResponse(**cfg.to_dict())


@router.post("/rewrite-preview", response_model=RewritePreviewResponse)
def rewrite_preview(body: RewritePreviewRequest) -> RewritePreviewResponse:
    """预览单条 query 的规则改写结果（不触发检索）"""
    store = get_knowledge_store()
    cfg = store.get_rewrite_config()
    rewriter = RuleBasedQueryRewriter(config=cfg)
    result = rewriter.rewrite(body.query)
    return RewritePreviewResponse(**result.to_dict())


@router.get("/citation-config", response_model=CitationConfigResponse)
def get_citation_config() -> CitationConfigResponse:
    """返回引用溯源开关与展示参数"""
    cfg = get_knowledge_store().get_citation_config()
    return CitationConfigResponse(**cfg.to_dict())


@router.put("/citation-config", response_model=CitationConfigResponse)
def update_citation_config(body: CitationConfigRequest) -> CitationConfigResponse:
    """更新引用溯源策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = CitationConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_citation_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CitationConfigResponse(**cfg.to_dict())


@ro
```


---

## 二十六、phase3_route_review 建议

课后运行 `src/day37/phase3_route_review.py` 串联 Day25–34。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| citations 替代检索 | 展示层 |
| preview 与全文 | 截断展示 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 rewrite 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET route-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 route_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 20 tests  
10. 能解释翻牌测试  
11. 能对比 Day33  
12. 能预告 Day36 HyDE  
13. 能读 validate 源码  
14. 能解释 include_route_meta  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_citations 上限 10  
19. 能解释 platform_version  
20. 能复述 ZL-NA-REQ-042 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`fetch_citations` 是 **Facade**：对外返回 dict，对内调用 RoutingRetriever.search。与 Day33 Facade 叠加。

---

## 三十、完整测试文件（API）

```python
"""Day 42 Approval API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from agent.approval_checkpoint import approval_checkpoint_store
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_approval_config_default(client):
    data = client.get("/api/agent/approval-config").json()
    assert data["enabled"] is True
    assert data["mock_auto_approve"] is True


def test_put_approval_config(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员A",
            "reject_message": "驳回",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mock_auto_approve"] is False


def test_approval_preview_rag_auto(client):
    resp = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "human_approval" in data["checkpoint_id"]
    assert data["approval_status"] == "approved"


def test_approval_interrupt_resume(client):
    client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员",
            "reject_message": "审批未通过",
        },
    )
    preview = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["interrupted"] is True
    cid = body["checkpoint_id"]
    assert cid

    resume = client.post(
        "/api/agent/approval-resume",
        json={"checkpoint_id": cid, "approved": True, "comment": "通过"},
    )
    assert resume.status_code == 200
    assert resume.json()["approval_status"] == "approved"


def test_status_includes_approval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["approval_config"]["enabled"] is True


def test_chat_approval_mode(client):
    resp = client.post(
        "/api/chat",
        json={"message": "年化收益", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert body.get("approval")
    assert body.get("graph_trace")


def test_chat_approval_mode_faq(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert "faq_lookup" in (body.get("tools_used") or [])


def test_invalid_reviewer_label_422(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": True,
            "reviewer_label": "",
            "reject_message": "x",
        },
    )
    assert resp.status_code == 422
```


---

## 三十一、课堂录音稿（8 min）

「打开 approval_workflow_graph，看审批节点。先看 require_rag_approval；命中则中断并返回 checkpoint_id，resume 后续跑。这就是 ZL-NA-REQ-042 的执行路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RAGContextService + RouteConfig
- GET/PUT /api/knowledge/route-config
- tests/day37 (20 cases)
```

---

## 三十三、context 二次嵌入

```python
"""
RAG 上下文构建服务 — 检索结果拼接为 Prompt context

将 doc_reader → chunker → retriever 串联，供 IntentRouter 的 query_context_provider 使用。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.citation_builder import CitationBundle, build_citation_bundle
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.query_expander import ExpansionResult
from rag.query_rewriter import RewriteResult
from rag.query_router import RouteResult
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever
from rag.retriever import KeywordRetriever, RetrievalResult
from tools.doc_reader import DocumentRecord, read_documents


Retriever = (
    KeywordRetriever
    | EmbeddingRetriever
    | ChromaEmbeddingRetriever
    | HybridRetriever
    | RerankingRetriever
    | RewritingRetriever
    | ExpandingRetriever
    | RoutingRetriever
)


@dataclass
class DocumentIndex:
    """文档索引：分块 + 检索器"""

    chunks: list[TextChunk] = field(default_factory=list)
    retriever: Retriever = field(default_factory=KeywordRetriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(query, top_k=top_k)


class RAGContextService:
    """
    RAG 上下文服务

    典型用法：
        service = RAGContextService.from_sample_docs()
        context = service.retrieve_context("年化收益率是多少？")
        router = IntentRouter(query_context_provider=service.retrieve_context)
    """

    def __init__(self, index: DocumentIndex | None = None) -> None:
        self.index = index or DocumentIndex()

    @classmethod
    def from_documents(
        cls,
        docs: list[DocumentRecord],
        *,
        chunk_size: int = 200,
        overlap: int = 40,
        use_cleaned: bool = True,
        use_embedding: bool = False,
    ) -> RAGContextService:
        chunks = chunk_documents(
            docs,
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=use_cleaned,
        )
        if use_embedding:
            retriever: Retriever = EmbeddingRetriever(chunks)
        else:
            retriever = KeywordRetriever(chunks)
        index = DocumentIndex(chunks=chunks, retriever=retriever)
        return cls(index)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        pattern: str = "*.txt",
        clean: bool = True,
        **kwargs,
    ) -> RAGContextService:
        docs = read_documents(directory, pattern=pattern, clean=clean)
        return cls.from_documents(docs, **kwargs)

    @classmethod
    def from_sample_docs(cls, *, use_embedding: bool = False, **kwargs) -> RAGContextService:
        return cls.from_directory(
            get_path("sample_docs"),
            use_embedding=use_embedding,
            **kwargs,
        )

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int = 3,
        max_chars: int = 800,
        separator: str = "\n---\n",
    ) -> str:
        """
        检索并拼接上下文文本。

        Args:
            query: 用户问题
            top_k: 检索块数量
            max_chars: 上下文总字符上限
            separator: 块之间的分隔符
        """
        query = (query or "").strip()
        if not query:
            return "（请输入检索问题）"

        results = self.index.search(query, top_k=top_k)
        if not results:
            return "（未检索到相关片段，请换关键词或扩充知识库）"

        parts: list[str] = []
        total = 0
        for i, result in enumerate(results, start=1):
            header = f"[片段{i}·{result.chunk.source}·sim={result.score:.0%}]"
            body = result.chunk.text.strip()
            piece = f"{header}\n{body}"
            if total + len(piece) > max_chars:
                remain = max_chars - total
                if remain <= 20:
                    break
                piece = piece[:remain] + "..."
            parts.append(piece)
            total += len(piece)
            if total >= max_chars:
                break

        return separator.join(parts)

    def retrieve_summary(self, query: str, *, top_k: int = 3) -> str:
        """返回检索结果摘要（供 /retrieve 命令）"""
        results = self.index.search(query, top_k=top_k)
        if not results:
            return "未命中任何片段"
        lines = [f"检索「{query}」共 {len(results)} 条："]
        for i, r in enumerate(results, start=1):
            kw = ", ".join(r.matched_tokens[:5]) or "—"
            lines.append(
                f"  {i}. score={r.score:.0%} source={r.chunk.source} 命中={kw}"
            )
            lines.append(f"     {r.preview(80)}")
        return "\n".join(lines)

    def retrieve_citation_bundle(
        self,
        query: str,
        *,
        top_k: int | None = None,
        config: CitationConfig | None = None,
        intent_override: str | None = None,
    ) -> CitationBundle:
        """
        检索并构建结构化引用包（含可选 rewrite 审计元数据）。

        供 /api/chat citations 与 citation-preview 使用。
        intent_override: 强制路由意图（如 rag_wide 重试召回）
        """
        cfg = config or CitationConfig()
        k = top_k if top_k is not None else cfg.max_citations
        query = (query or "").strip()
        if not query:
            return CitationBundle(citations=[], query="")

        retriever = self.index.retriever
        if intent_override is not None and hasattr(retriever, "search"):
            results = retriever.search(query, top_k=k, intent_override=intent_override)
        else:
            results = self.index.search(query, top_k=k)
        rewrite = _find_last_rewrite(self.index.retriever)
        expansion = _find_last_expansion(self.index.retriever)
        route = _find_last_route(self.index.retriever)

        return build_citation_bundle(
            query,
            results,
            config=cfg,
            rewrite=rewrite,
            expansion=expansion,
            route=route,
        )


def _find_last_rewrite(retriever: Retriever) -> RewriteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        if retriever.last_inner_rewrite is not None:
            return retriever.last_inner_rewrite
        return _find_last_rewrite(retriever.inner)
    if isinstance(retriever, RewritingRetriever):
        return retriever.last_rewrite
    return None


def _find_last_expansion(retriever: Retriever) -> ExpansionResult | None:
    if isinstance(retriever, RoutingRetriever):
        return _find_last_expansion(retriever.inner)
    if isinstance(retriever, ExpandingRetriever):
        return retriever.last_expansion
    return None


def _find_last_route(retriever: Retriever) -> RouteResult | None:
    if isinstance(retriever, RoutingRetriever):
        return retriever.last_route
    return None
```


---

## 三十四、route_demo 全文

```python
"""
人工审批工作流演示

运行：PYTHONPATH=src python3 src/day42/approval_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import ApprovalConfig
from api.factory import create_orchestrator
from day42.constants import APPROVAL_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 42 人工审批工作流演示")
    print("=" * 60)

    approval_checkpoint_store.clear()
    orchestrator = create_orchestrator()

    # mock 自动审批
    workflow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        graph_config=ApprovalConfig(max_iterations=3),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )
    for item in APPROVAL_CASES:
        outcome = workflow.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        has_approval = "human_approval" in outcome.checkpoint_id
        print(f"\n  Q: {item['query']}")
        print(f"    checkpoint_id={list(outcome.checkpoint_id)} approval={outcome.approval_status}")
        print(f"    tools={list(outcome.tools_used)} {tool} interrupted={outcome.interrupted}")

    # 中断 + 恢复
    print("\n  --- 中断恢复演示 ---")
    interrupt_flow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = interrupt_flow.invoke("年化收益怎么样")
    print(f"  interrupted={pending.interrupted} checkpoint={pending.checkpoint_id}")
    if pending.checkpoint_id:
        resumed = interrupt_flow.resume(pending.checkpoint_id, approved=True, comment="合规通过")
        print(f"  resumed reply: {resumed.reply[:80]}...")
        print(f"  status={resumed.approval_status}")

    print("\n  ✅ 审批工作流演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 三十五、延迟估算习题

pool=20，单次 rewrite 0.5ms → rewrite 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、口语命中 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rewrite 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_citations_count`、`rag_citation_enabled`、`chat_with_citations_rate`。

---

## 三十九、Citation JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | int | 1-based 排序 |
| chunk_id | str | 可追溯分块 |
| source | str | 文档名 |
| score | float | rerank 后分数 |
| preview | str | 截断正文 |
| matched_tokens | list | 命中 token |

---

## 四十、approval_workflow 全文嵌入

```python
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
from agent.graph_config import ApprovalConfig
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
    checkpoint_id: tuple[str, ...]
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
            "checkpoint_id": list(self.checkpoint_id),
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
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._graph_config = graph_config or ApprovalConfig()
        self._approval_config = approval_config or ApprovalConfig()
        self._graph = self._build_graph().compile()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        graph_config: ApprovalConfig | None = None,
        approval_config: ApprovalConfig | None = None,
    ) -> ApprovalWorkflowGraph:
        return cls(
            tools_from_executor(executor),
            graph_config=graph_config,
            approval_config=approval_config,
        )

    @property
    def graph_config(self) -> ApprovalConfig:
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
                checkpoint_id=(),
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
                checkpoint_id=[s.node for s in steps],
                checkpoint_id=state.checkpoint_id,
            )
            return ApprovalGraphOutcome(
                query=query,
                reply="等待人工审批，请通过 approval-resume 继续。",
                steps=tuple(steps),
                tools_used=tuple(dict.fromkeys(state.tools_used)),
                checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
            checkpoint_id=tuple(s.node for s in steps),
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
```


---

## 四十一、chat citations 代码

```python
if body.approval_mode and store.get_approval_config().enabled:
            gcfg = store.get_graph_config()
            acfg = store.get_approval_config()
            workflow = ApprovalWorkflowGraph.from_executor(
                orchestrator.tool_executor,
                graph_config=gcfg,
                approval_config=acfg,
            )
            history = _session_history(orchestrator, enabled=gcfg.use_session_history)
            approval_outcome = workflow.invoke(message, history=history)
            reply = approval_outcome.reply
            graph_trace = [s.to_dict() for s in approval_outcome.steps]
            tools_used = list(approval_outcome.tools_used)
            approval_payload = approval_outcome.approval
            orchestrator.assistant.history.add_user(message)
            if not approval_outcome.interrupted:
                orchestrator.assistant.history.add_assistant(reply)
        elif body.approval_mode and store.get_graph_config().enabled:
            cfg = store.get_graph_config()
            graph = ApprovalWorkflowGraph.from_executor(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            graph_outcome = graph.invoke(message, history=history)
            reply = graph_outcome.reply
            graph_trace = [s.to_dict() for s in graph_outcome.steps]
            tools_used = list(graph_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.executor_mode and store.get_executor_config().enabled:
            cfg = store.get_executor_config()
            agent = AgentExecutor.from_executor(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            exec_outcome = agent.invoke(message, history=history)
            reply = exec_outcome.reply
            executor_trace = [s.to_dict() for s in exec_outcome.steps]
            tools_used = list(exec_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.agent_mode and store.get_react_config().enabled:
            cfg = store.get_react_config()
            agent = ReActAgent(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            react_outcome = agent.run(message, history=history)
            reply = react_outcome.reply
            agent_trace = [s.to_dict() for s in react_outcome.steps]
            tools_used = list(react_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        else:
            reply = orchestrator.handle_message(message)
    except ConfigError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc
    except APIError as exc:
        raise _http_from_nexus(exc, status_code=502) from exc
    except NexusError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc

    kind, meta = classify_reply(reply)
    if dify_trace is not None:
        kind = "dify"
        meta = "Dify Workflow Bridge"
    elif mcp_trace is not None:
        kind = "mcp"
        meta = "MCP Tool Bridge"
    elif supervisor_trace is not None:
        kind = "supervisor"
        meta = "Supervisor Multi-Agent"
    elif approval_payload is not None:
        kind = "approval"
        meta = "Approval Workflow"
    elif graph_trace and kind != "approval":
        kind = "graph"
        meta = "StateGraph"
    elif executor_trace:
        kind = "executor"
        meta = "AgentExecutor"
    elif agent_trace:
        kind = "agent"
        meta = "ReAct Agent"
```


---

## 四十二、fetch_citations 代码

```python
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
```


---

## 四十三、前端展示要点

`app.js` 的 `msg__route` 渲染 rank/source/score/preview；`msg__rewrite` 展示改写链。

---

## 四十四、合规场景

理财回答必须带风险提示引用 — citations 第一条应来自风险揭示 chunk。

---

## 四十五、测试与 FR 映射

| 测试 | FR |
|------|-----|
| test_RuleBasedQueryRouter.route_from_results | FR-002 |
| test_fetch_citations_with_hits | FR-003 |
| test_chat_includes_citations | FR-006 |
| test_citation_preview_with_rewrite | FR-005 |

---

## 四十六、完整 context.py 引用段

```python
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
```


---

## 四十七、完整测试文件

```python
"""Day 42 ApprovalWorkflowGraph 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import ApprovalConfig
from api.factory import create_orchestrator


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def workflow():
    orch = create_orchestrator()
    return ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        graph_config=ApprovalConfig(max_iterations=4),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )


def test_approval_config_validate():
    ApprovalConfig().validate()
    with pytest.raises(ValueError):
        ApprovalConfig(reviewer_label="").validate()


def test_faq_skips_approval_node(workflow):
    outcome = workflow.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "human_approval" not in outcome.checkpoint_id
    assert outcome.approval_status in ("skipped", "approved")


def test_rag_with_mock_auto_approve(workflow):
    outcome = workflow.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert "human_approval" in outcome.checkpoint_id
    assert outcome.approval_status == "approved"
    assert not outcome.interrupted


def test_interrupt_and_resume_approve():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    assert pending.interrupted
    assert pending.checkpoint_id
    assert pending.approval_status == "pending"

    resumed = flow.resume(pending.checkpoint_id, approved=True, comment="OK")
    assert resumed.approval_status == "approved"
    assert resumed.reply
    assert not resumed.interrupted


def test_interrupt_and_resume_reject():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    resumed = flow.resume(pending.checkpoint_id, approved=False)
    assert resumed.approval_status == "rejected"
    assert "未通过" in resumed.reply or "审批" in resumed.reply


def test_approval_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_approval_config(
        ApprovalConfig(mock_auto_approve=False, reviewer_label="风控专员")
    )
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_approval_config()
    assert cfg.mock_auto_approve is False
    assert cfg.reviewer_label == "风控专员"


def test_resume_unknown_checkpoint():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(orch.tool_executor)
    outcome = flow.resume("missing-id", approved=True)
    assert outcome.approval_status == "error"
```


---

## 四十八、完整 API 测试

```python
"""Day 42 Approval API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from agent.approval_checkpoint import approval_checkpoint_store
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.45.0"


def test_get_approval_config_default(client):
    data = client.get("/api/agent/approval-config").json()
    assert data["enabled"] is True
    assert data["mock_auto_approve"] is True


def test_put_approval_config(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员A",
            "reject_message": "驳回",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["mock_auto_approve"] is False


def test_approval_preview_rag_auto(client):
    resp = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rag_search" in data["tools_used"]
    assert "human_approval" in data["checkpoint_id"]
    assert data["approval_status"] == "approved"


def test_approval_interrupt_resume(client):
    client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": False,
            "reviewer_label": "审核员",
            "reject_message": "审批未通过",
        },
    )
    preview = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["interrupted"] is True
    cid = body["checkpoint_id"]
    assert cid

    resume = client.post(
        "/api/agent/approval-resume",
        json={"checkpoint_id": cid, "approved": True, "comment": "通过"},
    )
    assert resume.status_code == 200
    assert resume.json()["approval_status"] == "approved"


def test_status_includes_approval_config(client):
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.45.0"
    assert status["approval_config"]["enabled"] is True


def test_chat_approval_mode(client):
    resp = client.post(
        "/api/chat",
        json={"message": "年化收益", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert body.get("approval")
    assert body.get("graph_trace")


def test_chat_approval_mode_faq(client):
    resp = client.post(
        "/api/chat",
        json={"message": "客服电话", "approval_mode": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "approval"
    assert "faq_lookup" in (body.get("tools_used") or [])


def test_invalid_reviewer_label_422(client):
    resp = client.put(
        "/api/agent/approval-config",
        json={
            "enabled": True,
            "require_rag_approval": True,
            "mock_auto_approve": True,
            "reviewer_label": "",
            "reject_message": "x",
        },
    )
    assert resp.status_code == 422
```


---

## 四十九、课堂 8 分钟录音稿

「打开 approval_workflow_graph，中断时返回 checkpoint_id。chat 里 approval 字段挂在 reply 后面。这就是 ZL-NA-REQ-042。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 4 · Day 42 · Approval · ZL-NA-REQ-042 · approval_workflow 精读完**
