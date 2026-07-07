"""
ChatAssistant 组件演示 — 不进入交互循环

运行：NEXUS_LLM_MOCK=1 python3 src/day14/assistant_demos.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from chat import ChatAssistant


def main() -> None:
    print("=== ChatAssistant 组件演示 ===\n")
    assistant = ChatAssistant()
    print(f"  历史消息数: {len(assistant.history)}")
    print(f"  客户端类型: {type(assistant.client).__name__}")
    print(f"  默认 system: {assistant.history.messages[0].content[:40]}...")

    _, help_msg, _ = assistant.handle_command("/help")
    print(f"\n{help_msg}")


if __name__ == "__main__":
    main()
