"""
流式 LLM 客户端演示 — Mock SSE 打字机效果

运行：NEXUS_LLM_MOCK=1 python3 src/day16/streaming_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from llm.streaming import StreamingLLMClient
from models import ChatMessage, ModelConfig


def main() -> int:
    print("=" * 52)
    print("  NexusAgent 流式输出演示")
    print("=" * 52)

    client = StreamingLLMClient(ModelConfig())
    print("\n  助手: ", end="", flush=True)

    result = client.stream_complete(
        [ChatMessage("user", "你好")],
        on_delta=lambda ch: print(ch, end="", flush=True),
    )

    print(f"\n\n  {result.usage_summary()}")
    print(f"  finish_reason: {result.finish_reason}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
