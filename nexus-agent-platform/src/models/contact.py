"""
通讯录联系人模型 — 继承 BaseModel

从 Day 8 contact_class 迁移至 models 包，纳入统一模型体系。

需求：ZL-NA-REQ-009
"""

from __future__ import annotations

from models.llm_base import BaseModel
from utils.validators import require_non_empty, validate_email, validate_phone


class Contact(BaseModel):
    """通讯录联系人实体"""

    def __init__(
        self,
        contact_id: int,
        name: str,
        phone: str,
        email: str,
        group: str = "未分组",
    ) -> None:
        self.id = contact_id
        self.name = (name or "").strip()
        self.phone = (phone or "").strip()
        self.email = (email or "").strip()
        self.group = (group or "").strip() or "未分组"

    def validate(self) -> str | None:
        for check in (
            require_non_empty(self.name, "姓名"),
            validate_phone(self.phone),
            validate_email(self.email),
        ):
            if check:
                return check
        if self.id <= 0:
            return "联系人 id 必须为正整数"
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "group": self.group,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Contact:
        return cls(
            contact_id=int(data.get("id", 0)),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            group=data.get("group", "未分组"),
        )

    def format_line(self) -> str:
        return f"#{self.id} {self.name} | {self.phone} | {self.email} | [{self.group}]"

    def __str__(self) -> str:
        return self.format_line()

    def __repr__(self) -> str:
        return f"Contact(id={self.id}, name={self.name!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return NotImplemented
        return self.to_dict() == other.to_dict()
