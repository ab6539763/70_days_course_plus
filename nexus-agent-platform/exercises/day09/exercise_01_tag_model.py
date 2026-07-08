"""
Day 9 作业练习 — Tag 模型骨架
"""

from __future__ import annotations

from models.llm_base import BaseModel


class Tag(BaseModel):
    def __init__(self, name: str) -> None:
        raise NotImplementedError

    def validate(self) -> str | None:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict) -> Tag:
        raise NotImplementedError
