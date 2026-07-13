"""
Supervisor 配置 — 多 Agent 委派与 trace 开关

需求：ZL-NA-REQ-043
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SupervisorConfig:
    """Supervisor 多 Agent 路由策略"""

    enabled: bool = True
    max_delegations: int = 1
    use_session_history: bool = True
    return_delegation_trace: bool = True
    mock_routing: bool = True

    def validate(self) -> None:
        if self.max_delegations < 1 or self.max_delegations > 3:
            raise ValueError(f"max_delegations 须在 1~3，收到 {self.max_delegations}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_delegations": self.max_delegations,
            "use_session_history": self.use_session_history,
            "return_delegation_trace": self.return_delegation_trace,
            "mock_routing": self.mock_routing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SupervisorConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_delegations=int(data.get("max_delegations", 1)),
            use_session_history=bool(data.get("use_session_history", True)),
            return_delegation_trace=bool(data.get("return_delegation_trace", True)),
            mock_routing=bool(data.get("mock_routing", True)),
        )
