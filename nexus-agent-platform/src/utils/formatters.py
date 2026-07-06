"""
格式化输出工具
"""

from __future__ import annotations

PRIORITY_LABELS = {1: "高", 2: "中", 3: "低"}


def format_box_report(title: str, lines: list[str], width: int = 42) -> str:
    """
    生成 ASCII 边框报告

    Args:
        title: 标题行
        lines: 内容行列表
        width: 边框宽度
    """
    border = "=" * width
    rows = [border, f"  {title}", border]
    rows.extend(f"  {line}" for line in lines)
    rows.append(border)
    return "\n".join(rows)


def format_todo_line(todo: dict) -> str:
    """格式化单条待办为显示行"""
    mark = "x" if todo.get("done") else " "
    pri = PRIORITY_LABELS.get(todo.get("priority", 2), "?")
    title = todo.get("title", "")
    tid = todo.get("id", "?")
    return f"[{mark}] #{tid} [{pri}] {title}"


def format_contact_line(contact: dict) -> str:
    """格式化单条通讯录记录"""
    cid = contact.get("id", "?")
    name = contact.get("name", "")
    phone = contact.get("phone", "")
    email = contact.get("email", "")
    group = contact.get("group", "未分组")
    return f"#{cid} {name} | {phone} | {email} | [{group}]"
