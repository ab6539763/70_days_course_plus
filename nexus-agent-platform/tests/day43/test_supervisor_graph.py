"""Day 43 SupervisorGraph 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.sub_agent import SUB_AGENTS
from agent.supervisor_config import SupervisorConfig
from agent.supervisor_graph import SupervisorGraph
from agent.supervisor_state import SupervisorState
from api.factory import create_orchestrator


@pytest.fixture
def graph():
    orch = create_orchestrator()
    return SupervisorGraph.from_executor(
        orch.tool_executor,
        config=SupervisorConfig(max_delegations=2),
    )


def test_supervisor_config_validate():
    SupervisorConfig().validate()
    with pytest.raises(ValueError):
        SupervisorConfig(max_delegations=0).validate()


def test_sub_agents_registry():
    names = {s.name for s in SUB_AGENTS}
    assert names == {"faq_worker", "rag_worker", "intent_worker"}


def test_supervisor_faq_delegation(graph):
    outcome = graph.invoke("客服电话多少")
    assert "faq_worker" in outcome.delegated_agents
    assert "faq_lookup" in outcome.tools_used
    assert "supervisor_route" in outcome.node_path


def test_supervisor_rag_delegation(graph):
    outcome = graph.invoke("年化收益怎么样")
    assert "rag_worker" in outcome.delegated_agents
    assert "rag_search" in outcome.tools_used


def test_supervisor_intent_delegation(graph):
    outcome = graph.invoke("帮我总结一下理财产品")
    assert "intent_worker" in outcome.delegated_agents
    assert "intent_classify" in outcome.tools_used


def test_supervisor_uses_history(graph):
    history = [{"role": "user", "content": "之前问过理财产品"}]
    outcome = graph.invoke("再查一下年化收益", history=history)
    assert outcome.reply
    assert any("supervisor_route" in n for n in outcome.node_path)


def test_supervisor_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_supervisor_config(SupervisorConfig(max_delegations=2))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_supervisor_config()
    assert cfg.max_delegations == 2


def test_supervisor_state_roundtrip():
    state = SupervisorState(query="q", delegated_agent="faq_worker")
    restored = SupervisorState.from_dict(state.to_dict())
    assert restored.delegated_agent == "faq_worker"
