"""
SSE 行解析演示

运行：python3 src/day16/sse_parse_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.paths import get_path
from llm.streaming import iter_sse_events, parse_stream_chunk


def main() -> None:
    path = get_path("stream_mock_sse")
    print("=== SSE 解析演示 ===\n")
    print(f"  文件: {path}\n")

    deltas: list[str] = []
    for event in iter_sse_events(path.read_text(encoding="utf-8").splitlines()):
        if event.get("done"):
            print("  → [DONE]")
            break
        chunk = parse_stream_chunk(event)
        if chunk.delta_content:
            deltas.append(chunk.delta_content)
            print(f"  delta: {chunk.delta_content!r}")

    print(f"\n  拼接结果: {''.join(deltas)}")


if __name__ == "__main__":
    main()
