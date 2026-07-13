"""Day 39 ReAct Agent 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.react_agent import ReActAgent
from agent.react_config import ReactConfig
from agent.react_parser import parse_react_block
from api.factory import create_orchestrator


@pytest.fixture
def agent():
    orch = create_orchestrator()
    return ReActAgent(orch.tool_executor, config=ReactConfig(max_steps=4))


def test_react_config_validate():
    ReactConfig().validate()
    with pytest.raises(ValueError):
        ReactConfig(max_steps=0).validate()


def test_parse_react_block_action():
    text = """Thought: 需要查 FAQ
Action: faq_lookup
Action Input: {"query": "客服电话"}"""
    parsed = parse_react_block(text)
    assert parsed.action == "faq_lookup"
    assert parsed.action_input["query"] == "客服电话"


def test_parse_react_block_final():
    text = "Thought: done\nFinal Answer: 请拨打 400-888-1234"
    parsed = parse_react_block(text)
    assert parsed.final_answer == "请拨打 400-888-1234"


def test_agent_faq_lookup(agent):
    outcome = agent.run("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert outcome.reply
    assert len(outcome.steps) >= 2


def test_agent_rag_search(agent):
    outcome = agent.run("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert outcome.reply


def test_agent_respects_max_steps():
    orch = create_orchestrator()
    agent = ReActAgent(orch.tool_executor, config=ReactConfig(max_steps=1))
    outcome = agent.run("年化收益怎么样")
    assert len([s for s in outcome.steps if s.action]) <= 1


def test_agent_uses_history(agent):
    history = [{"role": "user", "content": "之前问过理财产品"}]
    outcome = agent.run("再查一下年化收益", history=history)
    assert outcome.reply
    assert any("会话记忆" in (s.thought or "") for s in outcome.steps)


def test_react_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_react_config(ReactConfig(max_steps=5, mock_planner=True))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_react_config()
    assert cfg.max_steps == 5
