"""
聊天消息模型 — NexusAgent 对话系统的核心数据结构

继承 BaseModel，统一 validate / to_dict / from_dict 契约。

需求：ZL-NA-REQ-008 / ZL-NA-REQ-009
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

from models.llm_base import BaseModel

VALID_ROLES: tuple[str, ...] = ("system", "user", "assistant")

ROLE_LABELS: dict[str, str] = {
    "system": "系统",
    "user": "用户",
    "assistant": "助手",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ChatMessage(BaseModel):
    """
    单条聊天消息

    Attributes:
        role: 角色 system / user / assistant
        content: 消息正文
        created_at: ISO8601 时间戳
    """

    VALID_ROLES: ClassVar[tuple[str, ...]] = VALID_ROLES

    def __init__(
        self,
        role: str,
        content: str,
        *,
        created_at: str | None = None,
    ) -> None:
        self.role = (role or "").strip().lower()
        self.content = (content or "").strip()
        self.created_at = created_at or _now_iso()

    def validate(self) -> str | None:
        if self.role not in VALID_ROLES:
            return f"角色必须是 {', '.join(VALID_ROLES)} 之一"
        if not self.content:
            return "消息内容不能为空"
        return None

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChatMessage:
        return cls(
            role=data.get("role", ""),
            content=data.get("content", ""),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_api_response(cls, parsed: dict) -> ChatMessage:
        return cls(
            role=parsed.get("role") or "assistant",
            content=parsed.get("content", ""),
        )

    def is_system(self) -> bool:
        return self.role == "system"

    def is_user(self) -> bool:
        return self.role == "user"

    def is_assistant(self) -> bool:
        return self.role == "assistant"

    def format_line(self, *, max_content_len: int = 60) -> str:
        label = ROLE_LABELS.get(self.role, self.role)
        text = self.content
        if len(text) > max_content_len:
            text = text[: max_content_len - 3] + "..."
        return f"[{label}] {text}"

    def to_api_message(self) -> dict:
        return {"role": self.role, "content": self.content}

    def __str__(self) -> str:
        return self.format_line()

    def __repr__(self) -> str:
        preview = self.content[:20] + ("..." if len(self.content) > 20 else "")
        return f"ChatMessage(role={self.role!r}, content={preview!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChatMessage):
            return NotImplemented
        return (
            self.role == other.role
            and self.content == other.content
            and self.created_at == other.created_at
        )
