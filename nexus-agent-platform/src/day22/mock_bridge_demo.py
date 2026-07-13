"""
Mock 桥接逻辑演示 — 与 Day 21 编排器输出对照

运行：python3 src/day22/mock_bridge_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_REPO = _SRC.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chat import ChatAssistant, ChatOrchestrator, OrchestratorConfig
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from llm.token_counter import TokenCounter
from models import ModelConfig
from prompts import IntentRouter
from rag import RAGContextService
from services import SimilarQuestionMatcher
from tools import build_nexus_tools

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "mock"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}

QUERIES = [
    "投资有风险吗",
    "根据资料，年化收益率是多少？",
    "帮我总结要点",
]


def _build_orchestrator() -> ChatOrchestrator:
    import os

    os.environ.setdefault("NEXUS_LLM_MOCK", "1")
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
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        track_tokens=False,
    )
    return ChatOrchestrator(
        assistant,
        faq_matcher=faq,
        config=OrchestratorConfig(faq_direct_threshold=0.65),
    )


def main() -> int:
    print("=== Mock 桥接演示（后端 vs 前端契约）===\n")
    orch = _build_orchestrator()

    mock_js = (_REPO / "frontend" / "mock.js").read_text(encoding="utf-8")
    print(f"  frontend/mock.js 大小: {len(mock_js)} 字节\n")

    for q in QUERIES:
        reply = orch.handle_message(q)
        prefix = "FAQ" if reply.startswith("[FAQ") else "路由" if reply.startswith("[路由") else "其他"
        print(f"  Q: {q}")
        print(f"  后端({prefix}): {reply[:80]}...")
        print()

    print("  前端 mock.js 应在浏览器中复现相似前缀与语义。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
