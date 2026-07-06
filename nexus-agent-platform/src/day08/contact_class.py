"""
Contact 类 — 将 Day 7 dict 联系人升级为 OOP（预习作业参考实现）

与 ChatMessage 并列，展示「数据 + 行为」封装在同一类中。

需求：ZL-NA-REQ-008（选修）
"""

from __future__ import annotations

from utils.validators import require_non_empty, validate_email, validate_phone


class Contact:
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
        self.name = name.strip()
        self.phone = phone.strip()
        self.email = email.strip()
        self.group = group.strip() or "未分组"

    def validate(self) -> str | None:
        for check in (
            require_non_empty(self.name, "姓名"),
            validate_phone(self.phone),
            validate_email(self.email),
        ):
            if check:
                return check
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
