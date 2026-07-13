"""
AgentExecutor — LangChain 风格 invoke 循环，trace 与 Day 39 ReAct 对齐

复用 StructuredTool + mock planner，保证教学环境可测。

需求：ZL-NA-REQ-040
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agent.executor_config import ExecutorConfig
from agent.structured_tool import StructuredTool
from agent.tool_adapter import tool_map, tools_from_executor
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class ExecutorStep:
    """与 ReAct ReactStep 字段对齐，便于 agent_trace / executor_trace 互通"""

    step: int
    thought: str
    action: str | None = None
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str | None = None
    final_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "thought": self.thought,
            "action": self.action,
            "action_input": dict(self.action_input),
            "observation": self.observation,
            "final_answer": self.final_answer,
        }


@dataclass(frozen=True)
class ExecutorRunOutcome:
    query: str
    reply: str
    steps: tuple[ExecutorStep, ...]
    tools_used: tuple[str, ...]
    intermediate_steps: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
            "intermediate_steps": [
                {"action": a, "observation": o} for a, o in self.intermediate_steps
            ],
        }


class AgentExecutor:
    """框架式 Agent — tools + invoke，内部 mock planner 与 ReAct 规则一致"""

    def __init__(
        self,
        tools: list[StructuredTool],
        *,
        config: ExecutorConfig | None = None,
    ) -> None:
        self._tools = tools
        self._tool_by_name = tool_map(tools)
        self._tool_names = set(self._tool_by_name)
        self._config = config or ExecutorConfig()

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: ExecutorConfig | None = None,
    ) -> AgentExecutor:
        return cls(tools_from_executor(executor), config=config)

    @property
    def config(self) -> ExecutorConfig:
        return self._config

    @property
    def tools(self) -> list[StructuredTool]:
        return list(self._tools)

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> ExecutorRunOutcome:
        """LangChain 风格入口 — 返回 reply + intermediate_steps"""
        return self.run(query, history=history)

    def run(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> ExecutorRunOutcome:
        query = (query or "").strip()
        if not query:
            return ExecutorRunOutcome(
                query="",
                reply="请输入有效问题。",
                steps=(),
                tools_used=(),
                intermediate_steps=(),
            )

        cfg = self._config
        if not cfg.enabled:
            return ExecutorRunOutcome(
                query=query,
                reply="AgentExecutor 已关闭。",
                steps=(),
                tools_used=(),
                intermediate_steps=(),
            )

        steps: list[ExecutorStep] = []
        intermediate: list[tuple[str, str]] = []
        tools_used: list[str] = []
        last_observation: str | None = None
        reply = ""

        for step_idx in range(1, cfg.max_iterations + 1):
            if last_observation:
                reply = self._observation_to_answer(last_observation, query)
                hist_note = ""
                if history:
                    hist_note = f"（结合 {len(history)} 条会话记忆）"
                steps.append(
                    ExecutorStep(
                        step=step_idx,
                        thought=f"工具已返回，生成 Final Answer{hist_note}。",
                        final_answer=reply,
                    )
                )
                break

            thought, action, action_input, final = self._plan_step(
                query, step_idx, None, history=history
            )
            if final:
                steps.append(
                    ExecutorStep(
                        step=step_idx,
                        thought=thought,
                        final_answer=final,
                    )
                )
                reply = final
                break

            if not action or action not in self._tool_by_name:
                reply = "AgentExecutor 未能规划有效工具。"
                break

            observation = self._tool_by_name[action].run(action_input)
            last_observation = observation
            intermediate.append((action, observation))
            if not observation.strip().endswith("失败:"):
                tools_used.append(action)

            steps.append(
                ExecutorStep(
                    step=step_idx,
                    thought=thought,
                    action=action,
                    action_input=dict(action_input or {}),
                    observation=observation,
                )
            )
        else:
            if last_observation:
                reply = self._observation_to_answer(last_observation, query)
            else:
                reply = "未在迭代上限内得到答案，请换个问法。"

        return ExecutorRunOutcome(
            query=query,
            reply=reply,
            steps=tuple(steps),
            tools_used=tuple(dict.fromkeys(tools_used)),
            intermediate_steps=tuple(intermediate),
        )

    def _plan_step(
        self,
        query: str,
        step: int,
        observation: str | None,
        *,
        history: list[dict[str, str]] | None,
    ) -> tuple[str, str | None, dict[str, Any], str | None]:
        return self._mock_plan(query, step, observation, history=history)

    def _mock_plan(
        self,
        query: str,
        step: int,
        observation: str | None,
        *,
        history: list[dict[str, str]] | None,
    ) -> tuple[str, str | None, dict[str, Any], str | None]:
        if observation:
            answer = self._observation_to_answer(observation, query)
            hist_note = ""
            if history:
                hist_note = f"（结合 {len(history)} 条会话记忆）"
            return (
                f"StructuredTool 已返回，整理 Final Answer{hist_note}。",
                None,
                {},
                answer,
            )

        q = query.lower()
        hist_ctx = ""
        if history:
            last_user = [h["content"] for h in history if h.get("role") == "user"]
            if last_user:
                hist_ctx = f" 上文：{last_user[-1][:40]}"

        if "intent_classify" in self._tool_names and step == 1 and "总结" in q:
            return (
                f"Executor 选择 intent_classify StructuredTool。{hist_ctx}",
                "intent_classify",
                {"text": query},
                None,
            )

        if "faq_lookup" in self._tool_names and re.search(
            r"电话|客服|400|热线|联系", q
        ):
            return (
                f"Executor 选择 faq_lookup StructuredTool。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )

        if "rag_search" in self._tool_names:
            return (
                f"Executor 选择 rag_search StructuredTool。{hist_ctx}",
                "rag_search",
                {"query": query, "top_k": 3},
                None,
            )

        if "faq_lookup" in self._tool_names:
            return (
                f"Executor 回退 faq_lookup。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )

        return ("无可用 StructuredTool。", None, {}, "暂无法处理该问题。")

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
