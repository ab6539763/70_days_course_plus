"""
RAG 检索 + 意图路由 + ChatAssistant 联调

运行：NEXUS_LLM_MOCK=1 python3 src/day19/routed_rag_demo.py
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
from prompts import IntentRouter
from rag import RAGContextService


def main() -> int:
    print("=" * 56)
    print("  RAG 检索 + 意图路由 + ChatAssistant")
    print("=" * 56)

    rag = RAGContextService.from_sample_docs()
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env)

    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=rag,
        track_tokens=False,
    )

    script = [
        "/retrieve 年化收益率",
        "根据文档，年化收益率是多少？",
        "/route 请总结产品要点",
        "/exit",
    ]

    for line in script:
        print(f"\n>>> {line}")
        for out in assistant.run_scripted([line]):
            print(out)

    print("\n" + "=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
