"""
通讯录业务逻辑

将 CRUD 与查询封装为纯函数，供 CLI 与测试调用。
数据持久化通过 utils.json_utils 完成。

需求：ZL-NA-REQ-007
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from utils.json_utils import ensure_dict_keys, load_json, save_json
from utils.validators import require_non_empty, validate_email, validate_phone


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_store() -> dict:
    return {
        "version": "1.0",
        "next_id": 1,
        "contacts": [],
        "updated_at": now_iso(),
    }


def load_store(path: Path) -> dict:
    data = load_json(path, default=empty_store())
    ensure_dict_keys(data, {"version": "1.0", "next_id": 1, "contacts": []})
    return data


def save_store(path: Path, data: dict) -> None:
    data["updated_at"] = now_iso()
    save_json(path, data)


def create_contact(
    contact_id: int,
    name: str,
    phone: str,
    email: str,
    group: str = "未分组",
) -> dict:
    return {
        "id": contact_id,
        "name": name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "group": group.strip() or "未分组",
        "created_at": now_iso(),
    }


def validate_contact_fields(name: str, phone: str, email: str) -> str | None:
    """校验联系人字段，返回第一条错误消息"""
    for check in (
        require_non_empty(name, "姓名"),
        validate_phone(phone),
        validate_email(email),
    ):
        if check:
            return check
    return None


def add_contact(store: dict, name: str, phone: str, email: str, group: str = "未分组") -> tuple[dict | None, str | None]:
    """
    向 store 添加联系人

    Returns:
        (contact, error_message)
    """
    err = validate_contact_fields(name, phone, email)
    if err:
        return None, err
    contact = create_contact(store["next_id"], name, phone, email, group)
    store["contacts"].append(contact)
    store["next_id"] += 1
    return contact, None


def find_contact(contacts: list, contact_id: int) -> dict | None:
    for c in contacts:
        if c.get("id") == contact_id:
            return c
    return None


def delete_contact(store: dict, contact_id: int) -> bool:
    before = len(store["contacts"])
    store["contacts"] = [c for c in store["contacts"] if c.get("id") != contact_id]
    return len(store["contacts"]) < before


def search_by_name(contacts: list, keyword: str) -> list:
    kw = (keyword or "").strip().lower()
    if not kw:
        return list(contacts)
    return [c for c in contacts if kw in c.get("name", "").lower()]


def search_by_group(contacts: list, group: str) -> list:
    g = (group or "").strip()
    if not g:
        return list(contacts)
    return [c for c in contacts if c.get("group", "") == g]


def update_contact(contact: dict, *, name: str | None = None, phone: str | None = None, email: str | None = None, group: str | None = None) -> str | None:
    """原地更新联系人字段，返回错误消息"""
    new_name = name if name is not None else contact.get("name", "")
    new_phone = phone if phone is not None else contact.get("phone", "")
    new_email = email if email is not None else contact.get("email", "")
    err = validate_contact_fields(new_name, new_phone, new_email)
    if err:
        return err
    contact["name"] = new_name.strip()
    contact["phone"] = new_phone.strip()
    contact["email"] = new_email.strip()
    if group is not None:
        contact["group"] = group.strip() or "未分组"
    contact["updated_at"] = now_iso()
    return None


def group_stats(contacts: list) -> dict[str, int]:
    stats: dict[str, int] = {}
    for c in contacts:
        g = c.get("group", "未分组")
        stats[g] = stats.get(g, 0) + 1
    return stats
