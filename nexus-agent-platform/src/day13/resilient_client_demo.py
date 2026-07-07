"""
ResilientLLMClient 演示 — Mock + 模拟瞬时故障

运行：NEXUS_LLM_MOCK=1 python3 src/day13/resilient_client_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from core.exceptions import APIError
from core.paths import get_path
from llm.env import LLMEnvConfig
from llm.resilient_client import ResilientLLMClient
from llm.retry import RetryPolicy
from models import ChatMessage, ModelConfig

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "重试后成功。"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
}


def make_flaky_transport(fail_times: int = 2):
    state = {"n": 0}
    sample_path = get_path("chat_completion_sample")
    base = __import__("json").loads(sample_path.read_text(encoding="utf-8"))

    def transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict:
        state["n"] += 1
        print(f"  transport 调用 #{state['n']}")
        if state["n"] <= fail_times:
            raise APIError("service unavailable", status_code=503)
        return base

    return transport


def main() -> int:
    print("=" * 52)
    print("  ResilientLLMClient 演示（Mock + 503 重试）")
    print("=" * 52)

    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    policy = RetryPolicy(max_attempts=4, base_delay=0.05, backoff_factor=2.0, timeout_seconds=10)

    client = ResilientLLMClient(
        ModelConfig(),
        env=env,
        transport=make_flaky_transport(fail_times=2),
        policy=policy,
        on_retry_log=True,
    )

    result = client.complete([ChatMessage("user", "测试重试")])
    print(f"\n  回复: {result.message.content}")
    print(f"  {result.usage_summary()}")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
