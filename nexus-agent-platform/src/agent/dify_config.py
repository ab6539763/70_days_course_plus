"""
Dify 配置 — Nexus 工具链导出为 Dify 工作流 DSL

需求：ZL-NA-REQ-045
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DifyConfig:
    """Dify 工作流导出与追踪映射策略"""

    enabled: bool = True
    workflow_name: str = "nexus-agent-workflow"
    include_start_end: bool = True
    mock_routing: bool = True
    use_session_history: bool = True
    return_dify_trace: bool = True
    max_nodes: int = 10

    def validate(self) -> None:
        if self.max_nodes < 1 or self.max_nodes > 50:
            raise ValueError(f"max_nodes 须在 1~50，收到 {self.max_nodes}")
        if not (self.workflow_name or "").strip():
            raise ValueError("workflow_name 不能为空")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "workflow_name": self.workflow_name,
            "include_start_end": self.include_start_end,
            "mock_routing": self.mock_routing,
            "use_session_history": self.use_session_history,
            "return_dify_trace": self.return_dify_trace,
            "max_nodes": self.max_nodes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DifyConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            workflow_name=str(data.get("workflow_name", "nexus-agent-workflow")),
            include_start_end=bool(data.get("include_start_end", True)),
            mock_routing=bool(data.get("mock_routing", True)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_dify_trace=bool(data.get("return_dify_trace", True)),
            max_nodes=int(data.get("max_nodes", 10)),
        )
