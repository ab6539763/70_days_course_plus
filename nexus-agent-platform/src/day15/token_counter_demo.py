"""
Token 计数器演示 — API usage 与本地估算对比

运行：python3 src/day15/token_counter_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.response import ChatCompletionResult
from llm.token_counter import TokenCounter
from models import ChatMessage


def main() -> None:
    print("=" * 50)
    print("  NexusAgent Token 计数器")
    print("=" * 50)

    messages = [
        ChatMessage("system", "你是企业助手。"),
        ChatMessage("user", "请解释 token 是什么？"),
    ]

    counter = TokenCounter()
    estimated = counter.estimate_messages(messages)
    print(f"\n  本地估算 prompt tokens: {estimated}")

    # 模拟 API 返回的 usage（来自 Day 5 样本量级）
    result = ChatCompletionResult(
        message=ChatMessage("assistant", "Token 是大模型处理文本的最小单位。"),
        model="deepseek-chat",
        prompt_tokens=42,
        completion_tokens=18,
        total_tokens=60,
    )

    usage = counter.usage_from_result(result, messages)
    cost = counter.estimate_cost(usage)

    print(f"  API 回报: {usage.format_line()}")
    print(f"  费用估算: {cost.format_yuan()}")
    print(f"  {counter.compare_estimate(usage)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
