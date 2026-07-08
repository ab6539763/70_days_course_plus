"""
asyncio 入门演示 — Day 13 异步预习

运行：python3 src/day13/async_demos.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


async def fetch_label(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} OK"


async def main_async() -> None:
    print("=== asyncio.gather 并发 ===\n")
    results = await asyncio.gather(
        fetch_label("doc_reader", 0.1),
        fetch_label("llm_client", 0.1),
        fetch_label("retry", 0.1),
    )
    for item in results:
        print(f"  ✅ {item}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
