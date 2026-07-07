"""Day 18 意图分类器测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chat.cli_assistant import ChatAssistant
from llm.client import LLMClient
from llm.env import LLMEnvConfig
from models import ModelConfig
from prompts import IntentRouter, RuleBasedIntentClassifier

SAMPLE = {
    "model": "deepseek-chat",
    "choices": [{"message": {"role": "assistant", "content": "好的"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
}


def test_classify_rag_qa():
    m = RuleBasedIntentClassifier().classify("请根据文档说明收益率")
    assert m.template_name == "rag_qa"
    assert m.confidence > 0.5


def test_classify_doc_summary():
    m = RuleBasedIntentClassifier().classify("帮我总结要点")
    assert m.template_name == "doc_summary"


def test_classify_compliance():
    m = RuleBasedIntentClassifier().classify("审阅宣传语是否合规")
    assert m.template_name == "compliance_review"


def test_classify_product_faq():
    m = RuleBasedIntentClassifier().classify("理财产品收益怎么样")
    assert m.template_name == "product_faq"


def test_classify_general_fallback():
    m = RuleBasedIntentClassifier().classify("你好")
    assert m.template_name == "default_assistant"
    assert m.intent == "general"


def test_router_build_variables_rag():
    router = IntentRouter(context_provider=lambda: "ctx")
    match = router.classify("根据资料查询")
    vars_ = router.build_variables(match)
    assert vars_["context"] == "ctx"


def test_router_build_variables_compliance():
    router = IntentRouter()
    match = router.classify("请审查这段文案")
    vars_ = router.build_variables(match)
    assert "text" in vars_


def test_route_and_apply_changes_template():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    router = IntentRouter()
    assistant = ChatAssistant(client=client, track_tokens=False)
    match = router.route_and_apply(assistant, "请总结文档要点")
    assert match.template_name == "doc_summary"
    assert assistant.prompt_template is not None
    assert assistant.prompt_template.name == "doc_summary"


def test_assistant_auto_route():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    router = IntentRouter()
    a = ChatAssistant(client=client, intent_router=router, auto_route=True, track_tokens=False)
    reply = a.chat_turn("理财产品收益如何？")
    assert a.prompt_template is not None
    assert a.prompt_template.name == "product_faq"
    assert "路由" in reply or "好的" in reply


def test_assistant_route_command():
    env = LLMEnvConfig(api_key="x", base_url="https://api.example.com/v1", mock=True)
    client = LLMClient(ModelConfig(), env=env, transport=lambda *_: SAMPLE)
    router = IntentRouter()
    a = ChatAssistant(client=client, intent_router=router, track_tokens=False)
    handled, msg, _ = a.handle_command("/route 总结要点")
    assert handled
    assert "doc_summary" in msg


def test_intent_match_summary():
    m = RuleBasedIntentClassifier().classify("总结")
    assert "意图=" in m.summary()


def test_priority_compliance_over_rag():
    """同时命中合规与文档关键词时，合规优先"""
    m = RuleBasedIntentClassifier().classify("请根据文档审阅宣传语合规风险")
    assert m.template_name == "compliance_review"
