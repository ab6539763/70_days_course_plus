"""
Sprint 1 知识回顾 — Day 1-14 能力串联

运行：python3 src/day14/sprint1_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MILESTONES = [
    ("Day 1-3", "CLI 与环境"),
    ("Day 4-5", "数据结构 + JSON"),
    ("Day 6-7", "函数 + 通讯录"),
    ("Day 8-9", "OOP + BaseModel"),
    ("Day 10", "包结构重组"),
    ("Day 11", "doc_reader"),
    ("Day 12", "llm/client"),
    ("Day 13", "retry 装饰器"),
    ("Day 14", "cli_assistant ← 今日"),
]


def main() -> None:
    print("=== Sprint 1 能力里程碑 ===\n")
    for phase, desc in MILESTONES:
        print(f"  ✅ {phase}: {desc}")
    print("\n  阶段项目一：命令行多轮对话 AI 助手已交付。")


if __name__ == "__main__":
    main()
