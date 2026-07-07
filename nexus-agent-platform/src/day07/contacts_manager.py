"""
NexusAgent 通讯录管理系统 — Sprint 1 收官交付

综合运用 Day 1-6 技能：
    - 流程控制菜单（Day 3）
    - dict + JSON 持久化（Day 5）
    - utils 工具库（Day 6）
    - 函数化业务层 contact_service（Day 7）

需求：ZL-NA-REQ-007

使用方式（从 nexus-agent-platform 目录）：
    python3 src/day07/contacts_manager.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from utils.formatters import format_box_report, format_contact_line  # noqa: E402

_DAY07 = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("day07_constants", _DAY07 / "constants.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

_svc_spec = importlib.util.spec_from_file_location("day07_contact_service", _DAY07 / "contact_service.py")
SVC = importlib.util.module_from_spec(_svc_spec)
_svc_spec.loader.exec_module(SVC)

DATA_PATH = _SRC_ROOT / C.CONTACTS_FILE_REL


def show_menu() -> None:
    print()
    print(format_box_report(
        f"{C.APP_NAME} v{C.APP_VERSION}",
        [
            "1. 添加联系人",
            "2. 查看全部",
            "3. 按姓名搜索",
            "4. 按部门/分组筛选",
            "5. 编辑联系人",
            "6. 删除联系人",
            "7. 分组统计",
            "8. 立即保存",
            "0. 退出并保存",
        ],
    ))


def display_contacts(contacts: list) -> None:
    print("\n--- 通讯录 ---")
    if not contacts:
        print("  （暂无联系人）")
        return
    for c in contacts:
        print(f"  {format_contact_line(c)}")
    print()


def handle_add(store: dict) -> None:
    print("\n  【添加联系人】")
    name = input("  姓名：").strip()
    phone = input("  手机：").strip()
    email = input("  邮箱：").strip()
    group = input(f"  分组 [{C.DEFAULT_GROUP}]：").strip() or C.DEFAULT_GROUP
    contact, err = SVC.add_contact(store, name, phone, email, group)
    if err:
        print(f"  ⚠️  {err}")
        return
    print(f"  ✅ 已添加 #{contact['id']} {contact['name']}")


def handle_search_name(store: dict) -> None:
    kw = input("\n  姓名关键词：").strip()
    results = SVC.search_by_name(store["contacts"], kw)
    print(f"\n  找到 {len(results)} 条")
    display_contacts(results)


def handle_search_group(store: dict) -> None:
    group = input("\n  分组名称：").strip()
    results = SVC.search_by_group(store["contacts"], group)
    print(f"\n  [{group or '全部'}] 共 {len(results)} 条")
    display_contacts(results)


def handle_edit(store: dict) -> None:
    display_contacts(store["contacts"])
    raw = input("  编辑 ID：").strip()
    if not raw.isdigit():
        print("  ⚠️  无效 ID")
        return
    contact = SVC.find_contact(store["contacts"], int(raw))
    if not contact:
        print("  ⚠️  未找到")
        return
    print("  （直接回车保留原值）")
    name = input(f"  姓名 [{contact['name']}]：").strip() or None
    phone = input(f"  手机 [{contact['phone']}]：").strip() or None
    email = input(f"  邮箱 [{contact['email']}]：").strip() or None
    group = input(f"  分组 [{contact.get('group', C.DEFAULT_GROUP)}]：").strip() or None
    err = SVC.update_contact(contact, name=name, phone=phone, email=email, group=group)
    if err:
        print(f"  ⚠️  {err}")
    else:
        print("  ✅ 已更新")


def handle_delete(store: dict) -> None:
    display_contacts(store["contacts"])
    raw = input("  删除 ID：").strip()
    if not raw.isdigit():
        print("  ⚠️  无效 ID")
        return
    if SVC.delete_contact(store, int(raw)):
        print("  ✅ 已删除")
    else:
        print("  ⚠️  未找到")


def handle_stats(store: dict) -> None:
    stats = SVC.group_stats(store["contacts"])
    print("\n--- 分组统计 ---")
    if not stats:
        print("  （暂无数据）")
        return
    for group, count in sorted(stats.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {group}: {count} 人")
    print()


def main() -> None:
    store = SVC.load_store(DATA_PATH)
    print(f"\n已加载 {len(store['contacts'])} 位联系人 — Sprint 1 收官项目")
    print(f"数据文件: {DATA_PATH}")

    while True:
        show_menu()
        choice = input("请选择：").strip()

        if choice == "0":
            SVC.save_store(DATA_PATH, store)
            print(f"\n已保存，再见！\n")
            break
        elif choice == "1":
            handle_add(store)
        elif choice == "2":
            display_contacts(store["contacts"])
        elif choice == "3":
            handle_search_name(store)
        elif choice == "4":
            handle_search_group(store)
        elif choice == "5":
            handle_edit(store)
        elif choice == "6":
            handle_delete(store)
        elif choice == "7":
            handle_stats(store)
        elif choice == "8":
            SVC.save_store(DATA_PATH, store)
            print("  ✅ 已保存")
        else:
            print("  ⚠️  无效选择")


if __name__ == "__main__":
    main()
