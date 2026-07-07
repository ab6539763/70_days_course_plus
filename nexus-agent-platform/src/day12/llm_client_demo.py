"""
LLM 客户端演示 — Mock 模式（无需真实 API Key）

运行：NEXUS_LLM_MOCK=1 python3 src/day12/llm_client_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# CI 默认 Mock，避免泄露 Key 依赖
os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from day12.constants import DEFAULT_SYSTEM_PROMPT
from llm import LLMClient
from models import ChatMessage, ModelConfig


def main() -> int:
    print("=" * 52)
    print("  NexusAgent LLM Client 演示（Mock 模式）")
    print("=" * 52)

    client = LLMClient(
        ModelConfig(temperature=0.5, max_tokens=512),
    )
    print(f"  模式: {'Mock' if client.env.mock else 'Live'}")
    print(f"  模型: {client.config.model}")
    print(f"  URL:  {client.env.chat_completions_url}\n")

    messages = [
        ChatMessage("system", DEFAULT_SYSTEM_PROMPT),
        ChatMessage("user", "请用一句话介绍 NexusAgent 平台。"),
    ]

    result = client.complete(messages)
    print("  --- Assistant 回复 ---")
    print(f"  {result.message.content}\n")
    print(f"  finish_reason: {result.finish_reason}")
    print(f"  {result.usage_summary()}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
