"""
NexusAgent 待办管理器 v3 — 基于 utils 重构

使用 src/utils/ 工具库，消除重复代码。
数据文件仍使用 day05/data/todos.json。

需求：ZL-NA-REQ-006

使用方式（从 nexus-agent-platform 目录）：
    PYTHONPATH=src python src/day06/todo_manager_v3.py
    或
    python src/day06/todo_manager_v3.py  # 脚本自动添加 src 到 path

作者：NexusAgent 项目组
创建日期：2026-07-11
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# 将 src/ 加入路径以 import utils
_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from utils.formatters import format_box_report, format_todo_line  # noqa: E402
from utils.json_utils import ensure_dict_keys, load_json, save_json  # noqa: E402
from utils.validators import parse_positive_int, parse_priority, require_non_empty  # noqa: E402

import importlib.util

_DAY06 = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("day06_constants", _DAY06 / "constants.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

TODOS_PATH = _SRC_ROOT / C.TODOS_FILE_REL


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_store() -> dict:
    return {"version": "1.0", "next_id": 1, "todos": [], "updated_at": _now_iso()}


def load_store() -> dict:
    data = load_json(TODOS_PATH, default=empty_store())
    ensure_dict_keys(data, {"version": "1.0", "next_id": 1, "todos": []})
    return data


def save_store(data: dict) -> None:
    data["updated_at"] = _now_iso()
    save_json(TODOS_PATH, data)


def create_todo(todo_id: int, title: str, desc: str, priority: int) -> dict:
    return {
        "id": todo_id,
        "title": title,
        "description": desc,
        "priority": priority,
        "done": False,
        "created_at": _now_iso(),
    }


def find_todo(todos: list, todo_id: int) -> dict | None:
    for t in todos:
        if t.get("id") == todo_id:
            return t
    return None


def show_menu() -> None:
    print()
    print(format_box_report(
        f"{C.APP_NAME} v{C.APP_VERSION}",
        [
            "1. 添加待办",
            "2. 查看全部",
            "3. 标记完成",
            "4. 删除待办",
            "5. 按优先级排序",
            "6. 统计",
            "7. 立即保存",
            "0. 退出并保存",
        ],
    ))


def display_todos(todos: list, *, sorted_by_priority: bool = False) -> None:
    print("\n--- 待办列表 ---")
    if not todos:
        print("  （暂无）")
        return
    items = sorted(todos, key=lambda t: t.get("priority", 2)) if sorted_by_priority else todos
    for t in items:
        print(f"  {format_todo_line(t)}")
        if t.get("description"):
            print(f"       {t['description']}")
    print()


def handle_add(store: dict) -> None:
    title = input("\n  标题：").strip()
    err = require_non_empty(title, "标题")
    if err:
        print(f"  ⚠️  {err}")
        return
    desc = input("  描述：").strip()
    pri = parse_priority(input("  优先级 1/2/3 [2]：").strip())
    todo = create_todo(store["next_id"], title, desc, pri)
    store["todos"].append(todo)
    store["next_id"] += 1
    print(f"  ✅ 已添加 #{todo['id']}")


def handle_complete(store: dict) -> None:
    display_todos(store["todos"])
    tid = parse_positive_int(input("  完成 ID："))
    if tid is None:
        print("  ⚠️  无效 ID")
        return
    t = find_todo(store["todos"], tid)
    if t:
        t["done"] = True
        print("  ✅ 已标记完成")
    else:
        print("  ⚠️  未找到")


def handle_delete(store: dict) -> None:
    display_todos(store["todos"])
    tid = parse_positive_int(input("  删除 ID："))
    if tid is None:
        return
    store["todos"] = [t for t in store["todos"] if t.get("id") != tid]
    print("  ✅ 已删除")


def handle_stats(store: dict) -> None:
    todos = store["todos"]
    total = len(todos)
    done = sum(1 for t in todos if t.get("done"))
    print(f"\n  总计 {total}，已完成 {done}，未完成 {total - done}\n")


def main() -> None:
    store = load_store()
    print(f"\n已加载 {len(store['todos'])} 条待办（utils 重构版 v3）")

    while True:
        show_menu()
        choice = input("请选择：").strip()

        if choice == "0":
            save_store(store)
            print(f"\n已保存到 {TODOS_PATH}，再见！\n")
            break
        elif choice == "1":
            handle_add(store)
        elif choice == "2":
            display_todos(store["todos"])
        elif choice == "3":
            handle_complete(store)
        elif choice == "4":
            handle_delete(store)
        elif choice == "5":
            display_todos(store["todos"], sorted_by_priority=True)
        elif choice == "6":
            handle_stats(store)
        elif choice == "7":
            save_store(store)
            print("  ✅ 已保存")
        else:
            print("  ⚠️  无效选择")


if __name__ == "__main__":
    main()
