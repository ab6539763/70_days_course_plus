"""
CLI 助手 + Token 追踪演示

运行：NEXUS_LLM_MOCK=1 python3 src/day15/assistant_token_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from chat import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [
        {"message": {"role": "assistant", "content": "Token 是计费单位。"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 55, "completion_tokens": 12, "total_tokens": 67},
}


def main() -> int:
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, track_tokens=True)

    print("=== ChatAssistant + Token 追踪 ===\n")
    outputs = assistant.run_scripted(["什么是 token？", "/tokens"])
    for line in outputs:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
