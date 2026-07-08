"""
Sprint 3 知识回顾 — Day 15-21 能力串联

运行：python3 src/day21/sprint3_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MILESTONES = [
    ("Day 15", "Token 计算器 token_counter"),
    ("Day 16", "流式输出 streaming"),
    ("Day 17", "Prompt 模板库 prompts/"),
    ("Day 18", "意图分类 IntentRouter"),
    ("Day 19", "RAG 关键词检索 KeywordRetriever"),
    ("Day 20", "Embedding 检索 + FAQ 匹配"),
    ("Day 21", "工具编排 ChatOrchestrator ← 今日"),
]


def main() -> int:
    print("=== Sprint 3 能力里程碑（Day 15-21）===\n")
    for phase, desc in MILESTONES:
        print(f"  ✅ {phase}: {desc}")
    print("\n  周测交付：多轮对话 + FAQ 直答 + RAG + 工具调用整合")
    print("  下一阶段：Day 22-24 网页版 Chat（FastAPI + 前端）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
