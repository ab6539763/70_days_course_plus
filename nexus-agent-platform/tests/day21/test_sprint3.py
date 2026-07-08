"""Day 21 Sprint 3 周测与工具整合测试。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat import ChatAssistant, ChatOrchestrator, OrchestratorConfig
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from llm.token_counter import TokenCounter
from models import ModelConfig
from prompts import IntentRouter
from rag import RAGContextService
from services import SimilarQuestionMatcher
from tools import ToolExecutor, build_nexus_tools

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
}

DAY21 = SRC / "day21"


def _load_quiz():
    spec = importlib.util.spec_from_file_location("sprint3_quiz_test", DAY21 / "sprint3_quiz.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sprint3_quiz_has_10_questions():
    quiz = _load_quiz()
    assert len(quiz.QUESTIONS) == 10


def test_sprint3_quiz_scripted_full_score():
    quiz = _load_quiz()
    assert quiz.run_quiz_scripted() == 100


def test_sprint3_quiz_scripted_fail():
    quiz = _load_quiz()
    wrong = [3] * len(quiz.QUESTIONS)  # 各题选项数不足 4 的会 clamp，用 3 确保全错
    score = quiz.run_quiz_scripted(wrong)
    assert score == 0


def test_build_nexus_tools_registers_four():
    rag = RAGContextService.from_sample_docs(use_embedding=True)
    faq = SimilarQuestionMatcher()
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    registry = build_nexus_tools(
        faq_matcher=faq,
        rag_service=rag,
        intent_router=router,
        token_counter=TokenCounter(),
    )
    names = registry.list_names()
    assert "faq_lookup" in names
    assert "rag_search" in names
    assert "intent_classify" in names
    assert "estimate_tokens" in names


def test_tool_executor_faq_lookup():
    faq = SimilarQuestionMatcher()
    registry = build_nexus_tools(faq_matcher=faq)
    executor = ToolExecutor(registry)
    result = executor.execute("faq_lookup", {"query": "投资回报率怎么算"})
    assert result.success
    assert "收益" in result.output or "FAQ" in result.output


def test_tool_executor_rag_search():
    rag = RAGContextService.from_sample_docs(use_embedding=True)
    registry = build_nexus_tools(rag_service=rag)
    executor = ToolExecutor(registry)
    result = executor.execute("rag_search", {"query": "年化收益"})
    assert result.success
    assert len(result.output) > 10


def test_tool_executor_unknown_tool():
    registry = build_nexus_tools()
    executor = ToolExecutor(registry)
    result = executor.execute("not_exist", {})
    assert not result.success


def test_orchestrator_faq_direct():
    faq = SimilarQuestionMatcher()
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, track_tokens=False)
    orch = ChatOrchestrator(
        assistant,
        faq_matcher=faq,
        config=OrchestratorConfig(faq_direct_threshold=0.5),
    )
    reply = orch.handle_message("投资有风险吗")
    assert "FAQ 直答" in reply
    assert "风险" in reply


def test_orchestrator_fallback_to_llm():
    rag = RAGContextService.from_sample_docs(use_embedding=True)
    router = IntentRouter(query_context_provider=rag.retrieve_context)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        track_tokens=False,
    )
    orch = ChatOrchestrator(assistant, faq_matcher=SimilarQuestionMatcher(threshold=0.99))
    reply = orch.handle_message("根据资料查询收益率")
    assert "路由" in reply or "好的" in reply


def test_assistant_tool_command():
    faq = SimilarQuestionMatcher()
    registry = build_nexus_tools(faq_matcher=faq)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, tool_registry=registry, track_tokens=False)
    handled, msg, _ = assistant.handle_command("/tool list")
    assert handled
    assert "faq_lookup" in msg


def test_assistant_tool_execute():
    faq = SimilarQuestionMatcher()
    router = IntentRouter()
    registry = build_nexus_tools(faq_matcher=faq, intent_router=router)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, tool_registry=registry, track_tokens=False)
    handled, msg, _ = assistant.handle_command("/tool intent_classify 总结要点")
    assert handled
    assert "doc_summary" in msg or "意图" in msg


def test_integrated_demo_imports():
    spec = importlib.util.spec_from_file_location(
        "integrated_demo_test", DAY21 / "integrated_assistant_demo.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)
