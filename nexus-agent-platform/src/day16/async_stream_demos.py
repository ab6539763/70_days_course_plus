"""
asyncio 流式消费预习 — Day 16 异步扩展

运行：python3 src/day16/async_stream_demos.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.streaming import mock_stream_from_text


async def consume_stream_async(text: str) -> str:
    """异步迭代 mock stream（教学用包装）"""
    transport = mock_stream_from_text(text)
    parts: list[str] = []

    def _iter_chunks():
        yield from transport("http://mock", {}, {})

    for raw in await asyncio.to_thread(lambda: list(_iter_chunks())):
        from llm.streaming import parse_stream_chunk

        chunk = parse_stream_chunk(raw)
        if chunk.delta_content:
            parts.append(chunk.delta_content)
            await asyncio.sleep(0.01)

    return "".join(parts)


async def main_async() -> None:
    print("=== asyncio 消费流式 chunk ===\n")
    result = await consume_stream_async("异步流式")
    print(f"  结果: {result}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
