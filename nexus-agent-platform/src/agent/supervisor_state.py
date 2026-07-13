"""
SupervisorState — 多 Agent 委派共享状态

需求：ZL-NA-REQ-043
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupervisorState:
    """Supervisor 与子 Agent 间传递的状态"""

    query: str = ""
    reply: str = ""
    delegated_agent: str | None = None
    routing_reason: str = ""
    worker_tool: str | None = None
    worker_output: str | None = None
    tools_used: list[str] = field(default_factory=list)
    delegated_agents: list[str] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)
    done: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "delegated_agent": self.delegated_agent,
            "routing_reason": self.routing_reason,
            "worker_tool": self.worker_tool,
            "worker_output": self.worker_output,
            "tools_used": list(self.tools_used),
            "delegated_agents": list(self.delegated_agents),
            "history": list(self.history),
            "done": self.done,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SupervisorState:
        if not data:
            return cls()
        return cls(
            query=str(data.get("query", "")),
            reply=str(data.get("reply", "")),
            delegated_agent=data.get("delegated_agent"),
            routing_reason=str(data.get("routing_reason", "")),
            worker_tool=data.get("worker_tool"),
            worker_output=data.get("worker_output"),
            tools_used=list(data.get("tools_used") or []),
            delegated_agents=list(data.get("delegated_agents") or []),
            history=list(data.get("history") or []),
            done=bool(data.get("done", False)),
        )
