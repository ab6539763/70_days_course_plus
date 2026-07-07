"""
请求体组装演示 — ChatMessage + ModelConfig

运行：python3 src/day12/api_demos.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.client import build_request_body
from models import ChatMessage, ModelConfig


def main() -> None:
    print("=== Chat Completions 请求体预览 ===\n")
    config = ModelConfig(model="deepseek-chat", temperature=0.3, max_tokens=256)
    messages = [
        ChatMessage("system", "你是企业知识库助手。"),
        ChatMessage("user", "理财产品年化收益率是多少？"),
    ]
    body = build_request_body(messages, config)
    print(json.dumps(body, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
