"""
Token 原理演示 — 字符、词与 token 的关系

运行：python3 src/day15/token_principle_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.token_counter import estimate_tokens


def main() -> None:
    samples = [
        "Hello world",
        "你好世界",
        "NexusAgent 智链科技平台",
        "理财产品年化收益率约为 3.5%-4.2%",
    ]
    print("=== Token 估算演示（启发式）===\n")
    for text in samples:
        n = estimate_tokens(text)
        print(f"  文本: {text!r}")
        print(f"  字符数: {len(text)} | 估算 tokens: {n}\n")


if __name__ == "__main__":
    main()
