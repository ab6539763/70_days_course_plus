"""
Sprint 3 整合助手演示 — FAQ 直答 + 编排 + 工具

运行：NEXUS_LLM_MOCK=1 python3 src/day21/integrated_assistant_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from chat import ChatAssistant, ChatOrchestrator, OrchestratorConfig
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from llm.token_counter import TokenCounter
from models import ModelConfig
from prompts import IntentRouter
from rag import RAGContextService
from services import SimilarQuestionMatcher
from tools import ToolExecutor, build_nexus_tools


def main() -> int:
    print("=" * 58)
    print("  Sprint 3 整合助手 — FAQ + RAG + 意图 + 工具")
    print("=" * 58)

    rag = RAGContextService.from_sample_docs(use_embedding=True)
    faq = SimilarQuestionMatcher()
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    tools = build_nexus_tools(
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        token_counter=TokenCounter(),
    )

    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env)

    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=rag,
        faq_matcher=faq,
        tool_registry=tools,
        track_tokens=False,
    )

    orchestrator = ChatOrchestrator(
        assistant,
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        tool_registry=tools,
        config=OrchestratorConfig(faq_direct_threshold=0.65),
    )

    script = [
        "/tool list",
        "/tool faq_lookup 投资回报率怎么算",
        "有没有风险啊？",
        "根据资料，年化收益率是多少？",
        "/exit",
    ]

    for line in script:
        print(f"\n>>> {line}")
        if line.startswith("/"):
            for out in assistant.run_scripted([line]):
                print(out)
        else:
            reply = orchestrator.handle_message(line)
            print(f"编排器: {reply}")

    print("\n" + "=" * 58)
    return 0


if __name__ == "__main__":
    sys.exit(main())
