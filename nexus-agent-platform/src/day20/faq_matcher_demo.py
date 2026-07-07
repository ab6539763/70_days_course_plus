"""
相似问题匹配演示

运行：python3 src/day20/faq_matcher_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from services import SimilarQuestionMatcher

QUESTIONS = [
    "投资回报率怎么算？",
    "有没有风险啊？",
    "怎么打客服？",
    "pdf能传吗",
    "内部文件能发微信吗",
    "量子纠缠原理是什么",
]


def main() -> int:
    matcher = SimilarQuestionMatcher()
    print("=== 相似 FAQ 匹配 ===\n")

    for q in QUESTIONS:
        match = matcher.match(q)
        if match:
            print(f"  Q: {q}")
            print(f"  → {match.summary()}")
            print(f"    A: {match.entry.answer}\n")
        else:
            print(f"  Q: {q}")
            print("  → 未匹配\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
