"""
NexusAgent 待办管理器 v2 — dict + JSON 持久化

在 Day 4 list 版基础上升级：
    - 每条待办使用 dict 存储
    - 启动时从 data/todos.json 加载
    - 退出时自动保存

需求：ZL-NA-REQ-005

使用方式：
    python src/day05/todo_manager_v2.py

作者：NexusAgent 项目组
创建日期：2026-07-10
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _CURRENT_DIR.parent


def _load_module(name: str, filename: str):
    path = _CURRENT_DIR / filename
    spec = importlib.util.spec_from_file_location(f"day05_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load_module("constants", "constants.py")
storage = _load_module("storage", "todo_storage.py")

TODOS_PATH = _SRC_ROOT / C.TODOS_FILE_REL


def show_menu() -> None:
    print()
    print("=" * 44)
    print(f"  {C.APP_NAME} v{C.APP_VERSION}")
    print(f"  数据文件: {TODOS_PATH.name}")
    print("=" * 44)
    print("  1. 添加待办")
    print("  2. 查看全部")
    print("  3. 标记完成")
    print("  4. 删除待办")
    print("  5. 按优先级排序显示")
    print("  6. 统计")
    print("  7. 立即保存到 JSON")
    print("  0. 退出并保存")
    print("=" * 44)


def display_todos(todos: list, *, sorted_by_priority: bool = False) -> None:
    print("\n--- 待办列表 ---")
    if not todos:
        print("  （暂无）")
        return
    items = sorted(todos, key=lambda t: t["priority"]) if sorted_by_priority else todos
    for t in items:
        mark = "x" if t["done"] else " "
        pri = C.PRIORITY_LABELS.get(t["priority"], "?")
        print(f"  [{mark}] #{t['id']} [{pri}] {t['title']}")
        if t.get("description"):
            print(f"       {t['description']}")
    print()


def handle_add(store: dict) -> None:
    title = input("\n  标题：").strip()
    if not title:
        print("  ⚠️  标题不能为空")
        return
    desc = input("  描述：").strip()
    pri = input("  优先级 1/2/3 [2]：").strip() or "2"
    if pri not in ("1", "2", "3"):
        pri = "2"
    todo = storage.create_todo_dict(store["next_id"], title, desc, int(pri))
    store["todos"].append(todo)
    store["next_id"] += 1
    print(f"  ✅ 已添加 #{todo['id']}")


def handle_complete(store: dict) -> None:
    display_todos(store["todos"])
    s = input("  完成 ID：").strip()
    if not s.isdigit():
        return
    t = storage.find_todo_by_id(store["todos"], int(s))
    if t:
        t["done"] = True
        print("  ✅ 已标记完成")
    else:
        print("  ⚠️  未找到")


def handle_delete(store: dict) -> None:
    display_todos(store["todos"])
    s = input("  删除 ID：").strip()
    if not s.isdigit():
        return
    tid = int(s)
    store["todos"] = [t for t in store["todos"] if t["id"] != tid]
    print("  ✅ 已删除")


def handle_stats(store: dict) -> None:
    todos = store["todos"]
    total = len(todos)
    done = len([t for t in todos if t["done"]])
    print(f"\n  总计 {total}，已完成 {done}，未完成 {total - done}\n")


def main() -> None:
    store = storage.load_store(TODOS_PATH)
    print(f"\n已加载 {len(store['todos'])} 条待办（dict + JSON 版）")

    while True:
        show_menu()
        choice = input("请选择：").strip()

        if choice == "0":
            storage.save_store(TODOS_PATH, store)
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
            storage.save_store(TODOS_PATH, store)
            print(f"  ✅ 已保存到 {TODOS_PATH}")
        else:
            print("  ⚠️  无效选择")


if __name__ == "__main__":
    main()
