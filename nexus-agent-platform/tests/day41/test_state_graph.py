"""Day 41 StateGraph 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.graph_config import GraphConfig
from agent.graph_state import AgentGraphState
from agent.rag_agent_graph import RAGAgentGraph
from agent.state_graph import END, StateGraph
from api.factory import create_orchestrator


@pytest.fixture
def graph():
    orch = create_orchestrator()
    return RAGAgentGraph.from_executor(
        orch.tool_executor,
        config=GraphConfig(max_iterations=4),
    )


def test_graph_config_validate():
    GraphConfig().validate()
    with pytest.raises(ValueError):
        GraphConfig(max_iterations=0).validate()


def test_state_graph_compile_invoke():
    g = StateGraph()
    g.add_node("start", lambda s: AgentGraphState(query=s.query, reply="ok", done=True))
    g.set_entry_point("start")
    g.add_edge("start", END)
    compiled = g.compile()
    out = compiled.invoke(AgentGraphState(query="hi"))
    assert out.reply == "ok"
    assert out.done is True


def test_graph_faq_lookup(graph):
    outcome = graph.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert outcome.reply
    assert "planner" in outcome.node_path


def test_graph_rag_search(graph):
    outcome = graph.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert outcome.reply


def test_graph_respects_max_iterations():
    orch = create_orchestrator()
    agent = RAGAgentGraph.from_executor(
        orch.tool_executor,
        config=GraphConfig(max_iterations=1),
    )
    outcome = agent.invoke("年化收益怎么样")
    assert len(outcome.steps) >= 1


def test_graph_uses_history(graph):
    history = [{"role": "user", "content": "之前问过理财产品"}]
    outcome = graph.invoke("再查一下年化收益", history=history)
    assert outcome.reply
    assert any("planner" in s.node for s in outcome.steps)


def test_graph_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_graph_config(GraphConfig(max_iterations=5, mock_planner=True))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_graph_config()
    assert cfg.max_iterations == 5


def test_graph_state_roundtrip():
    state = AgentGraphState(query="q", tools_used=["faq_lookup"])
    restored = AgentGraphState.from_dict(state.to_dict())
    assert restored.query == "q"
    assert restored.tools_used == ["faq_lookup"]
