"""
ReAct Agent 配置 — 步数上限与开关

需求：ZL-NA-REQ-039
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReactConfig:
    """手写 ReAct 循环策略"""

    enabled: bool = True
    max_steps: int = 3
    use_session_history: bool = True
    mock_planner: bool = True

    def validate(self) -> None:
        if self.max_steps < 1 or self.max_steps > 8:
            raise ValueError(f"max_steps 须在 1~8，收到 {self.max_steps}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_steps": self.max_steps,
            "use_session_history": self.use_session_history,
            "mock_planner": self.mock_planner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ReactConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_steps=int(data.get("max_steps", 3)),
            use_session_history=bool(data.get("use_session_history", True)),
            mock_planner=bool(data.get("mock_planner", True)),
        )
