"""
AgentGraphState — LangGraph 风格共享状态

需求：ZL-NA-REQ-041 / ZL-NA-REQ-042
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
    approval_status: str = "skipped"
    interrupted: bool = False
    checkpoint_id: str | None = None
    approver_note: str | None = None
    pending_tool: str | None = None

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
            "approval_status": self.approval_status,
            "interrupted": self.interrupted,
            "checkpoint_id": self.checkpoint_id,
            "approver_note": self.approver_note,
            "pending_tool": self.pending_tool,
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
            approval_status=str(data.get("approval_status", "skipped")),
            interrupted=bool(data.get("interrupted", False)),
            checkpoint_id=data.get("checkpoint_id"),
            approver_note=data.get("approver_note"),
            pending_tool=data.get("pending_tool"),
        )
