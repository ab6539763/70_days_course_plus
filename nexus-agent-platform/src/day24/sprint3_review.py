"""
Sprint 3 收官回顾 — Day 15-24 全链路

运行：python3 src/day24/sprint3_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MILESTONES = [
    ("Day 15", "Token 计算器"),
    ("Day 16", "流式输出 streaming"),
    ("Day 17", "Prompt 模板库"),
    ("Day 18", "意图分类 IntentRouter"),
    ("Day 19", "RAG 关键词检索"),
    ("Day 20", "Embedding + FAQ 匹配"),
    ("Day 21", "工具编排 ChatOrchestrator"),
    ("Day 22", "frontend 静态聊天页"),
    ("Day 23", "FastAPI POST /api/chat"),
    ("Day 24", "网页版 Chat 完整整合 ← 今日"),
]

DELIVERABLES = [
    "frontend/ — 浏览器聊天 UI（session 持久化）",
    "src/api/ — REST API 薄层",
    "src/chat/orchestrator.py — 编排核心",
    "scripts/sprint3_demo.sh — 一条命令冒烟",
    "Sprint 3 投资人 5 分钟演示流程",
]


def main() -> int:
    print("=" * 58)
    print("  Sprint 3 收官回顾（Phase 2 · Day 15–24）")
    print("=" * 58)
    print("\n  能力里程碑:")
    for phase, desc in MILESTONES:
        print(f"    ✅ {phase}: {desc}")

    print("\n  阶段交付物:")
    for item in DELIVERABLES:
        print(f"    • {item}")

    print("\n  Phase 3 预告: RAG 知识库（Day 25+）")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
