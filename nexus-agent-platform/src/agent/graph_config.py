"""
StateGraph 配置 — 迭代上限与节点 trace 开关

需求：ZL-NA-REQ-041
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GraphConfig:
    """LangGraph 风格状态图策略"""

    enabled: bool = True
    max_iterations: int = 3
    use_session_history: bool = True
    return_node_trace: bool = True
    mock_planner: bool = True

    def validate(self) -> None:
        if self.max_iterations < 1 or self.max_iterations > 8:
            raise ValueError(f"max_iterations 须在 1~8，收到 {self.max_iterations}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_iterations": self.max_iterations,
            "use_session_history": self.use_session_history,
            "return_node_trace": self.return_node_trace,
            "mock_planner": self.mock_planner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GraphConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_iterations=int(data.get("max_iterations", 3)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_node_trace=bool(data.get("return_node_trace", True)),
            mock_planner=bool(data.get("mock_planner", True)),
        )
