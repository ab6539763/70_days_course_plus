"""
意图 → 模板变量构建演示

运行：python3 src/day18/router_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prompts import IntentRouter


def main() -> None:
    router = IntentRouter(context_provider=lambda: "样本上下文：年化 3.5%")
    queries = [
        "请总结这份报告的三个要点",
        "审查：本产品保证稳赚不赔",
    ]
    print("=== IntentRouter 变量构建 ===\n")
    for q in queries:
        match = router.classify(q)
        vars_ = router.build_variables(match)
        print(f"  Q: {q}")
        print(f"  {match.summary()}")
        print(f"  变量键: {list(vars_.keys())}\n")


if __name__ == "__main__":
    main()
