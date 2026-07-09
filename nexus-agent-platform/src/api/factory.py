"""
编排器工厂 — 为 API 会话构建 ChatOrchestrator

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

import os
from typing import Callable

from chat import ChatAssistant, ChatOrchestrator, OrchestratorConfig
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from llm.token_counter import TokenCounter
from models import ModelConfig
from prompts import IntentRouter
from rag.knowledge_store import get_knowledge_store
from rag import RAGContextService
from services import SimilarQuestionMatcher
from tools import build_nexus_tools

SAMPLE_MOCK = {
    "model": "deepseek-chat",
    "choices": [
        {
            "message": {"role": "assistant", "content": "好的，已收到您的问题。"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
}


def create_orchestrator(
    *,
    transport: Callable | None = None,
    faq_threshold: float = 0.65,
) -> ChatOrchestrator:
    """创建带完整 Sprint 3 能力的编排器实例"""
    os.environ.setdefault("NEXUS_LLM_MOCK", "1")

    rag = get_knowledge_store().as_rag_service()
    faq = SimilarQuestionMatcher()
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    tools = build_nexus_tools(
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        token_counter=TokenCounter(),
    )

    env = LLMEnvConfig(api_key="mock", base_url="https://api.example.com/v1", mock=True)
    if transport is None:
        transport = lambda *_a, **_k: SAMPLE_MOCK

    client = LLMClient(ModelConfig(), env=env, transport=transport)
    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=rag,
        faq_matcher=faq,
        tool_registry=tools,
        track_tokens=False,
    )

    return ChatOrchestrator(
        assistant,
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        tool_registry=tools,
        config=OrchestratorConfig(faq_direct_threshold=faq_threshold),
    )
