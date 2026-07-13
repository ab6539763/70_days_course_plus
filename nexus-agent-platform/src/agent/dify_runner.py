"""
DifyRunner — 复用 McpRunner 决策/执行，输出 Dify 工作流风格追踪 + 导出 DSL

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DifyWorkflow
from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from tools.executor import ToolExecutor


@dataclass(frozen=True)
class DifyRunOutcome:
    query: str
    reply: str
    dify_trace: tuple[dict[str, Any], ...]
    tools_used: tuple[str, ...]
    workflow_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "dify_trace": [dict(e) for e in self.dify_trace],
            "tools_used": list(self.tools_used),
            "workflow_name": self.workflow_name,
        }


class DifyRunner:
    """在 McpRunner 的 discover→route→call→answer 之上，附加 Dify 工作流语义"""

    def __init__(
        self,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> None:
        self._executor = executor
        self._config = config or DifyConfig()
        self._mcp = McpRunner.from_executor(
            executor,
            config=McpConfig(
                enabled=True,
                mock_routing=self._config.mock_routing,
                use_session_history=self._config.use_session_history,
                return_mcp_trace=True,
            ),
        )

    @classmethod
    def from_executor(
        cls,
        executor: ToolExecutor,
        *,
        config: DifyConfig | None = None,
    ) -> DifyRunner:
        return cls(executor, config=config)

    @property
    def config(self) -> DifyConfig:
        return self._config

    def export_workflow(self) -> DifyWorkflow:
        return build_dify_workflow(
            self._executor,
            workflow_name=self._config.workflow_name,
            include_start_end=self._config.include_start_end,
            max_nodes=self._config.max_nodes,
        )

    def invoke(
        self,
        query: str,
        *,
        history: list[dict[str, str]] | None = None,
    ) -> DifyRunOutcome:
        cfg = self._config
        if not (query or "").strip():
            return self._empty_outcome("", "请输入有效问题。")
        if not cfg.enabled:
            return self._empty_outcome(query, "Dify 工作流对接已关闭。")

        outcome = self._mcp.invoke(query, history=history)
        events = map_steps_to_dify_trace(outcome.steps) if cfg.return_dify_trace else []
        return DifyRunOutcome(
            query=outcome.query,
            reply=outcome.reply,
            dify_trace=tuple(e.to_dict() for e in events),
            tools_used=outcome.tools_used,
            workflow_name=cfg.workflow_name,
        )

    def _empty_outcome(self, query: str, reply: str) -> DifyRunOutcome:
        return DifyRunOutcome(
            query=query,
            reply=reply,
            dify_trace=(),
            tools_used=(),
            workflow_name=self._config.workflow_name,
        )
