"""
Day 8 作业 — 手写 ChatMessage 练习（骨架）

学员在下方补全 __init__、validate、to_dict。
"""

from __future__ import annotations


class ChatMessageExercise:
    VALID_ROLES = ("system", "user", "assistant")

    def __init__(self, role: str, content: str) -> None:
        raise NotImplementedError

    def validate(self) -> str | None:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError
