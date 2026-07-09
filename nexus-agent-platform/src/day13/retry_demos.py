"""
重试装饰器演示 — 模拟 429 限流后成功

运行：python3 src/day13/retry_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.exceptions import APIError
from llm.retry import retry


def main() -> None:
    print("=== retry 装饰器演示 ===\n")
    attempts = {"n": 0}

    @retry(max_attempts=4, base_delay=0.05, backoff_factor=2.0)
    def flaky_api() -> str:
        attempts["n"] += 1
        print(f"  第 {attempts['n']} 次调用")
        if attempts["n"] < 3:
            raise APIError("rate limited", status_code=429)
        return "success"

    result = flaky_api()
    print(f"\n  结果: {result}（共尝试 {attempts['n']} 次）")


if __name__ == "__main__":
    main()
