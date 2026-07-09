"""
待办数据 JSON 持久化

负责 todos.json 的读取与写入，隔离文件 IO 与业务逻辑。

需求：ZL-NA-REQ-005 (ZL-NA-020)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def empty_store() -> dict:
    """返回空的数据存储结构"""
    return {
        "version": "1.0",
        "next_id": 1,
        "todos": [],
        "updated_at": _now_iso(),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_store(path: Path) -> dict:
    """
    从 JSON 文件加载待办数据

    文件不存在时返回空存储，不抛异常。
    JSON 格式错误时抛出 json.JSONDecodeError。
    """
    if not path.exists():
        return empty_store()

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 基本结构校验与补全
    if "todos" not in data:
        data["todos"] = []
    if "next_id" not in data:
        data["next_id"] = max((t.get("id", 0) for t in data["todos"]), default=0) + 1
    if "version" not in data:
        data["version"] = "1.0"
    return data


def save_store(path: Path, data: dict) -> None:
    """将待办数据写入 JSON 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_todo_dict(todo_id: int, title: str, desc: str, priority: int) -> dict:
    """创建一条待办 dict 记录"""
    return {
        "id": todo_id,
        "title": title,
        "description": desc,
        "priority": priority,
        "done": False,
        "created_at": _now_iso(),
    }


def find_todo_by_id(todos: list, todo_id: int) -> dict | None:
    """在 todos 列表中按 id 查找 dict"""
    for t in todos:
        if t.get("id") == todo_id:
            return t
    return None
