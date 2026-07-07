"""
消息历史服务 — 从 day08 迁入 services 层

需求：ZL-NA-REQ-010
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import JsonParseError, ModelValidationError, StorageError
from models.message import ChatMessage
from utils.json_utils import load_json, save_json


class MessageHistoryService:
    """
    聊天消息历史容器（服务层）

    与 Day 8 MessageHistory 行为一致，增强异常处理。
    """

    def __init__(self, messages: list[ChatMessage] | None = None) -> None:
        self._messages: list[ChatMessage] = list(messages or [])

    @property
    def messages(self) -> list[ChatMessage]:
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def add(self, message: ChatMessage) -> str | None:
        """添加消息，返回错误消息或 None（与 Day 8 API 兼容）"""
        err = message.validate()
        if err:
            return err
        self._messages.append(message)
        return None

    def add_user(self, content: str) -> str | None:
        return self.add(ChatMessage("user", content))

    def add_assistant(self, content: str) -> str | None:
        return self.add(ChatMessage("assistant", content))

    def add_system(self, content: str) -> str | None:
        return self.add(ChatMessage("system", content))

    def last(self) -> ChatMessage | None:
        return self._messages[-1] if self._messages else None

    def to_api_messages(self) -> list[dict]:
        return [m.to_api_message() for m in self._messages]

    def save(self, path: Path) -> None:
        try:
            save_json(path, {"messages": [m.to_dict() for m in self._messages]})
        except OSError as exc:
            raise StorageError(f"写入失败: {exc}", path=str(path)) from exc

    def save_json(self, path: Path) -> None:
        """Day 8 兼容别名"""
        self.save(path)

    @classmethod
    def load(cls, path: Path) -> MessageHistoryService:
        data = load_json(path, default={"messages": []})
        if not isinstance(data, dict):
            raise JsonParseError("根节点必须是 object", path=str(path))
        items = data.get("messages", [])
        if not isinstance(items, list):
            raise JsonParseError("messages 必须是数组", path=str(path))
        messages = []
        for i, item in enumerate(items):
            obj, err = ChatMessage.from_dict_safe(item)
            if err:
                raise JsonParseError(f"messages[{i}]: {err}", path=str(path))
            messages.append(obj)
        return cls(messages)

    @classmethod
    def load_json(cls, path: Path) -> MessageHistoryService:
        """Day 8 兼容别名"""
        return cls.load(path)

    def to_dict_list(self) -> list[dict]:
        return [m.to_dict() for m in self._messages]

    @classmethod
    def from_dict_list(cls, items: list[dict]) -> MessageHistoryService:
        return cls([ChatMessage.from_dict(item) for item in items])

    def filter_by_role(self, role: str) -> list[ChatMessage]:
        role = role.strip().lower()
        return [m for m in self._messages if m.role == role]

    def display(self) -> None:
        if not self._messages:
            print("  （暂无消息）")
            return
        for i, msg in enumerate(self._messages, 1):
            print(f"  {i}. {msg.format_line()}")


# Day 8 兼容别名
MessageHistory = MessageHistoryService
