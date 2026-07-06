"""
输入校验工具

从各 day CLI 中抽取的重复校验逻辑。
"""

from __future__ import annotations

import re


def require_non_empty(value: str, field_name: str = "字段") -> str | None:
    """
    校验字符串非空

    Returns:
        错误消息，通过则返回 None
    """
    if value is None or not str(value).strip():
        return f"{field_name}不能为空"
    return None


def parse_priority(value: str, default: int = 2) -> int:
    """
    解析优先级 1/2/3

    Args:
        value: 用户输入
        default: 非法输入时的默认值
    """
    value = (value or "").strip()
    if value in ("1", "2", "3"):
        return int(value)
    return default


def parse_positive_int(value: str) -> int | None:
    """解析正整数，失败返回 None"""
    value = (value or "").strip()
    if value.isdigit() and int(value) > 0:
        return int(value)
    return None


def validate_email(email: str) -> str | None:
    """
    简单邮箱格式校验

    Returns:
        错误消息或 None
    """
    email = (email or "").strip()
    if not email:
        return "邮箱不能为空"
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return "邮箱格式不正确"
    return None
