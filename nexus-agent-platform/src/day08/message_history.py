"""
消息历史管理 — 多轮对话的消息列表容器

将多个 ChatMessage 组织为可持久化、可导出 API 格式的历史记录。

需求：ZL-NA-REQ-008
"""

from __future__ import annotations

from pathlib import Path

from models.message import ChatMessage
from utils.json_utils import load_json, save_json


class MessageHistory:
    """
    聊天消息历史容器

    内部使用 list[ChatMessage] 存储，提供增删查与 JSON 持久化。
    """

    def __init__(self, messages: list[ChatMessage] | None = None) -> None:
        self._messages: list[ChatMessage] = list(messages or [])

    @property
    def messages(self) -> list[ChatMessage]:
        """返回消息列表副本，防止外部直接修改内部状态"""
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def add(self, message: ChatMessage) -> str | None:
        """
        添加一条消息（校验通过后追加）

        Returns:
            错误消息或 None
        """
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

    def filter_by_role(self, role: str) -> list[ChatMessage]:
        role = role.strip().lower()
        return [m for m in self._messages if m.role == role]

    def to_api_messages(self) -> list[dict]:
        """导出为 LLM API 所需的 messages 数组"""
        return [m.to_api_message() for m in self._messages]

    def to_dict_list(self) -> list[dict]:
        return [m.to_dict() for m in self._messages]

    @classmethod
    def from_dict_list(cls, items: list[dict]) -> MessageHistory:
        return cls([ChatMessage.from_dict(item) for item in items])

    def save_json(self, path: Path) -> None:
        save_json(path, {"messages": self.to_dict_list()})

    @classmethod
    def load_json(cls, path: Path) -> MessageHistory:
        data = load_json(path, default={"messages": []})
        items = data.get("messages", [])
        return cls.from_dict_list(items)

    def display(self) -> None:
        """打印全部消息"""
        if not self._messages:
            print("  （暂无消息）")
            return
        for i, msg in enumerate(self._messages, 1):
            print(f"  {i}. {msg.format_line()}")
