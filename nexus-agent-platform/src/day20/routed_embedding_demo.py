"""
Embedding 检索 + 意图路由联调

运行：NEXUS_LLM_MOCK=1 python3 src/day20/routed_embedding_demo.py
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
from services import SimilarQuestionMatcher


def main() -> int:
    print("=" * 58)
    print("  Embedding RAG + 意图路由 + FAQ 匹配")
    print("=" * 58)

    rag = RAGContextService.from_sample_docs(use_embedding=True)
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    faq = SimilarQuestionMatcher()
    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env)

    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=rag,
        faq_matcher=faq,
        track_tokens=False,
    )

    script = [
        "/similar 投资回报率怎么算",
        "/retrieve 投资回报率",
        "根据资料，投资回报率是多少？",
        "/exit",
    ]

    for line in script:
        print(f"\n>>> {line}")
        for out in assistant.run_scripted([line]):
            print(out)

    print("\n" + "=" * 58)
    return 0


if __name__ == "__main__":
    sys.exit(main())
