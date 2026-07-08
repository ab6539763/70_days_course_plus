"""
NexusAgent 待办事项管理器

使用 list 存储待办项，练习增删改查、排序、列表推导式。
每项格式：[id, title, description, priority, done]

需求文档：ZL-NA-REQ-004

使用方式：
    python src/day04/todo_manager.py

作者：NexusAgent 项目组
创建日期：2026-07-09
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent


def _load_constants():
    spec = importlib.util.spec_from_file_location(
        "day04_constants", _CURRENT_DIR / "constants.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load_constants()


def create_todo(todo_id: int, title: str, desc: str, priority: int) -> list:
    """
    创建一条待办记录（list 格式）

    Args:
        todo_id: 唯一 ID
        title: 标题
        desc: 描述
        priority: 1高 2中 3低

    Returns:
        [id, title, desc, priority, done]
    """
    return [todo_id, title, desc, priority, False]


def find_by_id(todos: list, todo_id: int) -> list | None:
    """按 ID 查找待办"""
    for t in todos:
        if t[C.IDX_ID] == todo_id:
            return t
    return None


def find_index_by_id(todos: list, todo_id: int) -> int:
    """返回待办索引，未找到返回 -1"""
    for i, t in enumerate(todos):
        if t[C.IDX_ID] == todo_id:
            return i
    return -1


def add_todo(todos: list, next_id: int, title: str, desc: str, priority: int) -> int:
    """
    添加待办到 list 末尾

    Returns:
        下一个可用 ID
    """
    item = create_todo(next_id, title, desc, priority)
    todos.append(item)
    return next_id + 1


def mark_done(todos: list, todo_id: int) -> bool:
    """标记待办为完成"""
    t = find_by_id(todos, todo_id)
    if t is None:
        return False
    t[C.IDX_DONE] = True
    return True


def delete_todo(todos: list, todo_id: int) -> bool:
    """按 ID 删除待办"""
    idx = find_index_by_id(todos, todo_id)
    if idx < 0:
        return False
    todos.pop(idx)
    return True


def edit_todo(todos: list, todo_id: int, title: str | None, priority: int | None) -> bool:
    """编辑标题和/或优先级"""
    t = find_by_id(todos, todo_id)
    if t is None:
        return False
    if title is not None:
        t[C.IDX_TITLE] = title
    if priority is not None:
        t[C.IDX_PRIORITY] = priority
    return True


def get_stats(todos: list) -> tuple[int, int, int]:
    """
    统计待办数量

    Returns:
        (总数, 已完成, 未完成)
    """
    total = len(todos)
    done = len([t for t in todos if t[C.IDX_DONE]])
    pending = total - done
    return total, done, pending


def search_todos(todos: list, keyword: str) -> list:
    """列表推导式：按标题关键词搜索"""
    kw = keyword.lower()
    return [t for t in todos if kw in t[C.IDX_TITLE].lower()]


def display_todos(todos: list, *, sorted_by_priority: bool = False, title: str = "待办列表") -> None:
    """格式化打印待办列表"""
    print(f"\n--- {title} ---")
    if not todos:
        print("  （暂无待办）")
        return

    items = sorted(todos, key=lambda t: t[C.IDX_PRIORITY]) if sorted_by_priority else todos
    for t in items:
        mark = "x" if t[C.IDX_DONE] else " "
        pri = C.PRIORITY_LABELS.get(t[C.IDX_PRIORITY], "?")
        status = "已完成" if t[C.IDX_DONE] else "进行中"
        print(f"  [{mark}] #{t[C.IDX_ID]} [{pri}] {t[C.IDX_TITLE]} — {status}")
        if t[C.IDX_DESC]:
            print(f"       {t[C.IDX_DESC]}")
    print()


def show_menu() -> None:
    """显示主菜单"""
    print()
    print("=" * 42)
    print(f"  {C.APP_NAME} v{C.APP_VERSION}")
    print("=" * 42)
    print("  1. 添加待办")
    print("  2. 查看全部")
    print("  3. 标记完成")
    print("  4. 删除待办")
    print("  5. 编辑待办")
    print("  6. 按优先级排序显示")
    print("  7. 统计")
    print("  8. 关键词搜索")
    print("  0. 退出")
    print("=" * 42)


def read_priority(prompt: str = "优先级(1高/2中/3低)：") -> int:
    """读取并校验优先级"""
    while True:
        s = input(prompt).strip()
        if s in ("1", "2", "3"):
            return int(s)
        print("  ⚠️  请输入 1、2 或 3")


def handle_add(todos: list, next_id: int) -> int:
    """菜单 1：添加"""
    print("\n--- 添加待办 ---")
    title = input("  标题：").strip()
    if not title:
        print("  ⚠️  标题不能为空")
        return next_id
    desc = input("  描述（可空）：").strip()
    priority = read_priority()
    next_id = add_todo(todos, next_id, title, desc, priority)
    print(f"  ✅ 已添加 #{next_id - 1}")
    return next_id


def handle_mark_done(todos: list) -> None:
    """菜单 3：标记完成"""
    if not todos:
        print("  ⚠️  暂无待办")
        return
    display_todos(todos)
    s = input("  要完成的项目 ID：").strip()
    if not s.isdigit():
        print("  ⚠️  请输入数字 ID")
        return
    if mark_done(todos, int(s)):
        print("  ✅ 已标记完成")
    else:
        print("  ⚠️  未找到该 ID")


def handle_delete(todos: list) -> None:
    """菜单 4：删除"""
    if not todos:
        print("  ⚠️  暂无待办")
        return
    display_todos(todos)
    s = input("  要删除的项目 ID：").strip()
    if not s.isdigit():
        return
    todo_id = int(s)
    confirm = input(f"  确认删除 #{todo_id}？(y/n)：").strip().lower()
    if confirm != "y":
        print("  已取消")
        return
    if delete_todo(todos, todo_id):
        print("  ✅ 已删除")
    else:
        print("  ⚠️  未找到该 ID")


def handle_edit(todos: list) -> None:
    """菜单 5：编辑"""
    if not todos:
        print("  ⚠️  暂无待办")
        return
    display_todos(todos)
    s = input("  要编辑的项目 ID：").strip()
    if not s.isdigit():
        return
    todo_id = int(s)
    t = find_by_id(todos, todo_id)
    if t is None:
        print("  ⚠️  未找到")
        return
    new_title = input(f"  新标题（回车保持「{t[C.IDX_TITLE]}」）：").strip()
    new_pri = input("  新优先级 1/2/3（回车跳过）：").strip()
    title = new_title if new_title else None
    priority = int(new_pri) if new_pri in ("1", "2", "3") else None
    edit_todo(todos, todo_id, title, priority)
    print("  ✅ 已更新")


def handle_search(todos: list) -> None:
    """菜单 8：搜索"""
    kw = input("\n  搜索关键词：").strip()
    if not kw:
        return
    results = search_todos(todos, kw)
    display_todos(results, title=f"搜索结果「{kw}」")


def main() -> None:
    """主循环"""
    todos: list = []
    next_id = 1

    # 预置 Sprint 1 示例数据
    next_id = add_todo(todos, next_id, "完成文本清洗工具", "Day 2 已交付", 1)
    next_id = add_todo(todos, next_id, "实现平台 CLI 菜单", "Day 3 已交付", 1)
    next_id = add_todo(todos, next_id, "待办管理器", "Day 4 进行中", 2)

    print(f"\n欢迎使用 {C.APP_NAME}！")
    print("当前为内存存储，Day 5 将支持 JSON 持久化。")

    while True:
        show_menu()
        choice = input("请选择：").strip()

        if choice == "0":
            print("\n再见！今日待办已保存在内存中。\n")
            break
        elif choice == "1":
            next_id = handle_add(todos, next_id)
        elif choice == "2":
            display_todos(todos)
        elif choice == "3":
            handle_mark_done(todos)
        elif choice == "4":
            handle_delete(todos)
        elif choice == "5":
            handle_edit(todos)
        elif choice == "6":
            display_todos(todos, sorted_by_priority=True, title="按优先级排序")
        elif choice == "7":
            total, done, pending = get_stats(todos)
            print(f"\n  总计 {total}，已完成 {done}，未完成 {pending}\n")
        elif choice == "8":
            handle_search(todos)
        else:
            print("\n  ⚠️  无效选择，请输入 0-8")


if __name__ == "__main__":
    main()
