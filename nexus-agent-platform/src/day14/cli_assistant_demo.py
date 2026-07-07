"""
CLI 助手脚本演示 — Sprint 1 阶段项目验收脚本

模拟多轮对话，无需人工 input（CI 友好）。

运行：NEXUS_LLM_MOCK=1 python3 src/day14/cli_assistant_demo.py
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
from day14.constants import APP_NAME, APP_VERSION, SPRINT_NAME


def main() -> int:
    print("=" * 54)
    print(f"  {APP_NAME} v{APP_VERSION}")
    print(f"  {SPRINT_NAME} — 阶段项目一验收")
    print("=" * 54)

    assistant = ChatAssistant(on_retry_log=False)

    script = [
        "你好，请介绍一下 NexusAgent。",
        "/history",
        "理财产品收益率是多少？",
        "/save",
        "/exit",
    ]

    for line in script:
        print(f"\n>>> {line}")
        outputs = assistant.run_scripted([line])
        for out in outputs:
            print(out)

    print("\n" + "=" * 54)
    print("  验收完成")
    print("=" * 54)
    return 0


if __name__ == "__main__":
    sys.exit(main())
