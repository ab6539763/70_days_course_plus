"""
手写 ReAct Agent — Thought → Action → Observation 可观测工具链

复用 Day 21 ToolRegistry / ToolExecutor，在 mock 模式下用规则规划器保证可测。

需求：ZL-NA-REQ-039
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from agent.react_config import ReactConfig
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class ReactStep:
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
class ReactRunOutcome:
    query: str
    reply: str
    steps: tuple[ReactStep, ...]
    tools_used: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "steps": [s.to_dict() for s in self.steps],
            "tools_used": list(self.tools_used),
        }


class ReActAgent:
    """规则/mock ReAct 循环 — 调用 ToolExecutor 执行 Action"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: ReactConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or ReactConfig()
        self._tool_names = set(self._executor.registry.list_names())

    @property
    def config(self) -> ReactConfig:
        return self._config

    def run(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> ReactRunOutcome:
        query = (query or "").strip()
        if not query:
            return ReactRunOutcome(
                query="",
                reply="请输入有效问题。",
                steps=(),
                tools_used=(),
            )

        cfg = self._config
        if not cfg.enabled:
            return ReactRunOutcome(
                query=query,
                reply="ReAct Agent 已关闭。",
                steps=(),
                tools_used=(),
            )

        steps: list[ReactStep] = []
        tools_used: list[str] = []
        last_observation: str | None = None
        reply = ""

        for step_idx in range(1, cfg.max_steps + 1):
            if last_observation:
                reply = self._observation_to_answer(last_observation, query)
                hist_note = ""
                if history:
                    hist_note = f"（结合 {len(history)} 条会话记忆）"
                steps.append(
                    ReactStep(
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
                    ReactStep(
                        step=step_idx,
                        thought=thought,
                        final_answer=final,
                    )
                )
                reply = final
                break

            if not action:
                reply = "Agent 未能规划有效 Action。"
                break

            result = self._executor.execute(action, action_input)
            last_observation = result.summary()
            if result.success:
                tools_used.append(action)

            steps.append(
                ReactStep(
                    step=step_idx,
                    thought=thought,
                    action=action,
                    action_input=dict(action_input or {}),
                    observation=last_observation,
                )
            )
        else:
            if last_observation:
                reply = self._observation_to_answer(last_observation, query)
            else:
                reply = "未在步数上限内得到答案，请换个问法。"

        return ReactRunOutcome(
            query=query,
            reply=reply,
            steps=tuple(steps),
            tools_used=tuple(dict.fromkeys(tools_used)),
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
                f"工具已返回结果，整理 Final Answer{hist_note}。",
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
                f"用户需要总结类回答，先分类意图。{hist_ctx}",
                "intent_classify",
                {"text": query},
                None,
            )

        if "faq_lookup" in self._tool_names and re.search(
            r"电话|客服|400|热线|联系", q
        ):
            return (
                f"标准客服问题，优先 FAQ 直查。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )

        if "rag_search" in self._tool_names:
            return (
                f"需要知识库片段支撑，执行 rag_search。{hist_ctx}",
                "rag_search",
                {"query": query, "top_k": 3},
                None,
            )

        if "faq_lookup" in self._tool_names:
            return (
                f"回退 FAQ 匹配。{hist_ctx}",
                "faq_lookup",
                {"query": query},
                None,
            )

        return ("无可用工具。", None, {}, "暂无法处理该问题。")

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
