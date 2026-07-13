"""
消息历史 CLI — 手动构建多轮对话记录

演示 ChatMessage + MessageHistory 的完整用法。
数据保存到 day08/data/messages.json。

需求：ZL-NA-REQ-008

运行：python3 src/day08/message_cli.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from models.message import ChatMessage
from utils.formatters import format_box_report

_DAY08 = Path(__file__).resolve().parent
_spec_c = importlib.util.spec_from_file_location("day08_constants", _DAY08 / "constants.py")
C = importlib.util.module_from_spec(_spec_c)
_spec_c.loader.exec_module(C)

_spec_h = importlib.util.spec_from_file_location("day08_history", _DAY08 / "message_history.py")
HIST_MOD = importlib.util.module_from_spec(_spec_h)
_spec_h.loader.exec_module(HIST_MOD)

DATA_PATH = _SRC_ROOT / C.MESSAGES_FILE_REL


def show_menu() -> None:
    print()
    print(format_box_report(
        f"{C.APP_NAME} v{C.APP_VERSION}",
        [
            "1. 添加用户消息",
            "2. 添加助手消息",
            "3. 设置系统提示",
            "4. 查看全部消息",
            "5. 查看 API 格式导出",
            "6. 从 Day5 样例导入助手回复",
            "7. 立即保存",
            "0. 退出并保存",
        ],
    ))


def handle_import_sample(history: HIST_MOD.MessageHistory) -> None:
    """从 Day 5 chat_completion.json 导入 assistant 消息"""
    sample = _SRC_ROOT / "day05/sample_data/chat_completion.json"
    from utils.json_utils import load_json

    data = load_json(sample, default={})
    choices = data.get("choices", [])
    if not choices:
        print("  ⚠️  样例文件无 choices")
        return
    message = choices[0].get("message", {})
    msg = ChatMessage.from_dict(message)
    err = history.add(msg)
    if err:
        print(f"  ⚠️  {err}")
    else:
        print(f"  ✅ 已导入：{msg.format_line()}")


def main() -> None:
    history = HIST_MOD.MessageHistory.load_json(DATA_PATH)
    print(f"\n已加载 {len(history)} 条消息")
    if len(history) == 0:
        err = history.add_system(C.DEFAULT_SYSTEM_PROMPT)
        if err:
            print(f"  ⚠️  系统提示添加失败：{err}")
        else:
            print("  ℹ️  已自动添加默认 system 提示")

    while True:
        show_menu()
        choice = input("请选择：").strip()

        if choice == "0":
            history.save_json(DATA_PATH)
            print(f"\n已保存到 {DATA_PATH}，再见！\n")
            break
        elif choice == "1":
            text = input("\n  用户消息：").strip()
            err = history.add_user(text)
            print(f"  ⚠️  {err}" if err else "  ✅ 已添加")
        elif choice == "2":
            text = input("\n  助手消息：").strip()
            err = history.add_assistant(text)
            print(f"  ⚠️  {err}" if err else "  ✅ 已添加")
        elif choice == "3":
            text = input("\n  系统提示：").strip() or C.DEFAULT_SYSTEM_PROMPT
            # 替换或追加：简单起见追加新 system 消息
            err = history.add_system(text)
            print(f"  ⚠️  {err}" if err else "  ✅ 已添加 system")
        elif choice == "4":
            print("\n--- 消息历史 ---")
            history.display()
        elif choice == "5":
            print("\n--- API messages 格式 ---")
            import json
            print(json.dumps(history.to_api_messages(), ensure_ascii=False, indent=2))
        elif choice == "6":
            handle_import_sample(history)
        elif choice == "7":
            history.save_json(DATA_PATH)
            print("  ✅ 已保存")
        else:
            print("  ⚠️  无效选择")


if __name__ == "__main__":
    main()
