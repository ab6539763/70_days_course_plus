"""
AgentGraphState — LangGraph 风格共享状态

需求：ZL-NA-REQ-041
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentGraphState:
    """图节点间传递的可变状态"""

    query: str = ""
    reply: str = ""
    iteration: int = 0
    done: bool = False
    pending_action: str | None = None
    pending_input: dict[str, Any] = field(default_factory=dict)
    last_observation: str | None = None
    tools_used: list[str] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "iteration": self.iteration,
            "done": self.done,
            "pending_action": self.pending_action,
            "pending_input": dict(self.pending_input),
            "last_observation": self.last_observation,
            "tools_used": list(self.tools_used),
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AgentGraphState:
        if not data:
            return cls()
        return cls(
            query=str(data.get("query", "")),
            reply=str(data.get("reply", "")),
            iteration=int(data.get("iteration", 0)),
            done=bool(data.get("done", False)),
            pending_action=data.get("pending_action"),
            pending_input=dict(data.get("pending_input") or {}),
            last_observation=data.get("last_observation"),
            tools_used=list(data.get("tools_used") or []),
            history=list(data.get("history") or []),
        )
