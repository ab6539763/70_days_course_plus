"""Day 20 Embedding 与向量检索测试。"""

from __future__ import annotations

import math
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
from rag import (
    EmbeddingClient,
    EmbeddingRetriever,
    KeywordRetriever,
    RAGContextService,
    cosine_similarity,
    chunk_text,
)
from rag.chunker import TextChunk
from services import SimilarQuestionMatcher

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
}

NOTICE = "智链科技理财产品说明书。本产品年化收益率可达8%。投资有风险，入市需谨慎。"


def test_cosine_similarity_identical():
    v = [1.0, 2.0, 3.0]
    assert math.isclose(cosine_similarity(v, v), 1.0)


def test_cosine_similarity_orthogonal():
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_embedding_model_fit_and_embed():
    client = EmbeddingClient()
    client.fit_corpus(["年化收益", "风险提示"])
    vec = client.embed("年化收益")
    assert vec.dimension > 0
    assert len(vec.values) == vec.dimension


def test_embedding_similarity_synonym_pair():
    client = EmbeddingClient()
    client.fit_corpus([NOTICE, "FAQ 上传文档说明"])
    sim = client.similarity("投资回报率", NOTICE)
    assert sim > 0.15


def test_embedding_retriever_finds_synonym_query():
    chunks = chunk_text(NOTICE, chunk_size=200, source="notice.txt")
    retriever = EmbeddingRetriever(chunks)
    results = retriever.search("投资回报率是多少", top_k=1)
    assert results
    assert results[0].score > 0.1
    assert "收益" in results[0].chunk.text or "年化" in results[0].chunk.text


def test_keyword_vs_embedding_synonym():
    chunks = chunk_text(NOTICE, chunk_size=200, source="notice.txt")
    kw = KeywordRetriever(chunks).search("投资回报率", top_k=1)
    emb = EmbeddingRetriever(chunks).search("投资回报率", top_k=1)
    # 关键词可能未命中，向量应更可能命中
    assert emb
    if not kw:
        assert emb[0].score > 0


def test_rag_service_use_embedding():
    service = RAGContextService.from_sample_docs(use_embedding=True)
    assert isinstance(service.index.retriever, EmbeddingRetriever)
    context = service.retrieve_context("投资回报率", top_k=2)
    assert context and "未检索到" not in context


def test_faq_matcher_synonym_question():
    matcher = SimilarQuestionMatcher()
    match = matcher.match("投资回报率怎么算？")
    assert match is not None
    assert "收益" in match.entry.question or match.score > 0.3


def test_faq_matcher_risk_question():
    matcher = SimilarQuestionMatcher()
    match = matcher.match("有没有风险啊")
    assert match is not None
    assert match.entry.category == "risk"


def test_faq_matcher_no_match():
    matcher = SimilarQuestionMatcher()
    assert matcher.match("量子纠缠原理是什么") is None


def test_assistant_similar_command():
    matcher = SimilarQuestionMatcher()
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(client=client, faq_matcher=matcher, track_tokens=False)
    handled, msg, _ = assistant.handle_command("/similar 怎么联系客服")
    assert handled
    assert "客服" in msg


def test_assistant_embedding_rag_route():
    rag = RAGContextService.from_sample_docs(use_embedding=True)
    from prompts import IntentRouter

    router = IntentRouter(query_context_provider=rag.retrieve_context)
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    assistant = ChatAssistant(
        client=client,
        intent_router=router,
        auto_route=True,
        rag_service=rag,
        track_tokens=False,
    )
    reply = assistant.chat_turn("根据资料，投资回报率是多少？")
    assert assistant.prompt_template is not None
    assert "路由" in reply or "好的" in reply
