"""
意图路由 + ChatAssistant 自动选模板演示

运行：NEXUS_LLM_MOCK=1 python3 src/day18/routed_assistant_demo.py
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
from core.paths import get_path
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig
from prompts import IntentRouter
from tools.doc_reader import read_document


def _load_sample_context() -> str:
    doc = read_document(get_path("sample_docs") / "raw_notice.txt", clean=True)
    return (doc.cleaned or doc.content)[:400]


def main() -> int:
    print("=" * 54)
    print("  意图路由 + ChatAssistant 自动选模板")
    print("=" * 54)

    router = IntentRouter(context_provider=_load_sample_context)
    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env)

    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        track_tokens=False,
    )

    script = [
        "/route 请根据文档说明收益率",
        "根据资料，收益率是多少？",
        "/route 帮我审阅宣传语是否合规",
        "/exit",
    ]

    for line in script:
        print(f"\n>>> {line}")
        for out in assistant.run_scripted([line]):
            print(out)

    print("\n" + "=" * 54)
    return 0


if __name__ == "__main__":
    sys.exit(main())
