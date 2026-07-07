"""Day 19 RAG 检索入门测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant
from core.paths import get_path
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig
from prompts import IntentRouter
from rag import RAGContextService, chunk_text, chunk_documents
from tools.doc_reader import read_document, read_documents

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
}

LONG_TEXT = "第一段内容关于年化收益率可达8%。\n\n第二段说明投资有风险，入市需谨慎。\n\n第三段提供客服电话400-888-9999。"


def test_chunk_text_splits_with_overlap():
    chunks = chunk_text(LONG_TEXT, chunk_size=40, overlap=10, source="demo.txt")
    assert len(chunks) >= 2
    assert all(c.source == "demo.txt" for c in chunks)
    assert chunks[0].index == 0


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)


def test_chunk_documents_from_reader():
    docs = read_documents(get_path("sample_docs"), clean=True)
    chunks = chunk_documents(docs, chunk_size=150, overlap=20)
    assert len(chunks) >= 3
    sources = {c.source for c in chunks}
    assert "raw_notice.txt" in sources


def test_retriever_finds_yield_info():
    service = RAGContextService.from_sample_docs()
    results = service.index.search("年化收益率", top_k=2)
    assert results
    assert results[0].score > 0
    assert "收益" in results[0].chunk.text or "年化" in results[0].chunk.text


def test_retriever_finds_risk_notice():
    service = RAGContextService.from_sample_docs()
    context = service.retrieve_context("投资有风险吗", top_k=2)
    assert "风险" in context


def test_retrieve_context_respects_max_chars():
    service = RAGContextService.from_sample_docs()
    context = service.retrieve_context("收益率 风险 客服", top_k=5, max_chars=120)
    assert len(context) <= 130


def test_intent_router_query_context_provider():
    service = RAGContextService.from_sample_docs()
    router = IntentRouter(query_context_provider=service.retrieve_context)
    match = router.classify("请根据文档说明收益率")
    vars_ = router.build_variables(match)
    assert match.template_name == "rag_qa"
    assert "收益" in vars_["context"] or "年化" in vars_["context"]


def test_intent_router_static_context_fallback():
    router = IntentRouter(context_provider=lambda: "静态上下文")
    match = router.classify("根据资料查询")
    vars_ = router.build_variables(match)
    assert vars_["context"] == "静态上下文"


def test_route_and_apply_with_rag():
    service = RAGContextService.from_sample_docs()
    router = IntentRouter(query_context_provider=service.retrieve_context)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, track_tokens=False)
    match = router.route_and_apply(assistant, "根据文档查询年化收益")
    assert match.template_name == "rag_qa"
    assert assistant.prompt_template is not None
    assert "context" in assistant.template_variables


def test_assistant_retrieve_command():
    service = RAGContextService.from_sample_docs()
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, rag_service=service, track_tokens=False)
    handled, msg, _ = assistant.handle_command("/retrieve 客服电话")
    assert handled
    assert "score=" in msg


def test_assistant_auto_route_with_rag():
    service = RAGContextService.from_sample_docs()
    router = IntentRouter(query_context_provider=service.retrieve_context)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=service,
        track_tokens=False,
    )
    reply = assistant.chat_turn("根据资料，收益率是多少？")
    assert assistant.prompt_template is not None
    assert assistant.prompt_template.name == "rag_qa"
    assert "路由" in reply or "好的" in reply
