"""Day 45 Dify Bridge/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.dify_bridge import build_dify_workflow, map_steps_to_dify_trace
from agent.dify_config import DifyConfig
from agent.dify_protocol import DIFY_NODE_END, DIFY_NODE_START, DIFY_NODE_TOOL, DifyWorkflow
from agent.dify_runner import DifyRunner
from agent.mcp_runner import McpStep
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return DifyRunner.from_executor(orch.tool_executor, config=DifyConfig())


def test_dify_config_validate():
    DifyConfig().validate()
    with pytest.raises(ValueError):
        DifyConfig(max_nodes=0).validate()
    with pytest.raises(ValueError):
        DifyConfig(workflow_name="  ").validate()


def test_build_dify_workflow_has_start_and_end(runner):
    workflow = runner.export_workflow()
    assert isinstance(workflow, DifyWorkflow)
    types = [n.type for n in workflow.nodes]
    assert types[0] == DIFY_NODE_START
    assert types[-1] == DIFY_NODE_END
    assert any(t == DIFY_NODE_TOOL for t in types)


def test_build_dify_workflow_respects_max_nodes(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, max_nodes=1, include_start_end=True)
    tool_nodes = [n for n in workflow.nodes if n.type == DIFY_NODE_TOOL]
    assert len(tool_nodes) == 1


def test_build_dify_workflow_without_start_end(runner):
    orch = create_orchestrator()
    workflow = build_dify_workflow(orch.tool_executor, include_start_end=False)
    types = {n.type for n in workflow.nodes}
    assert DIFY_NODE_START not in types
    assert DIFY_NODE_END not in types


def test_dify_workflow_to_dict_shape(runner):
    workflow = runner.export_workflow()
    payload = workflow.to_dict()
    assert payload["app"]["mode"] == "workflow"
    assert "nodes" in payload["workflow"]["graph"]
    assert "edges" in payload["workflow"]["graph"]


def test_map_steps_to_dify_trace():
    steps = (
        McpStep(step=1, phase="discover", thought="发现工具"),
        McpStep(step=2, phase="route", thought="路由", tool="faq_lookup", arguments={"query": "x"}),
        McpStep(step=3, phase="call", thought="调用", tool="faq_lookup", observation="obs"),
        McpStep(step=4, phase="answer", thought="汇总", final_answer="reply"),
    )
    events = map_steps_to_dify_trace(steps)
    assert len(events) == 4
    assert events[0].node_type == DIFY_NODE_START
    assert events[-1].node_type == DIFY_NODE_END
    assert events[2].outputs.get("observation") == "obs"


def test_dify_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert len(outcome.dify_trace) == 4


def test_dify_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_dify_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_dify_runner_empty_query(runner):
    outcome = runner.invoke("")
    assert outcome.dify_trace == ()
    assert "有效问题" in outcome.reply


def test_dify_runner_disabled():
    orch = create_orchestrator()
    runner = DifyRunner.from_executor(orch.tool_executor, config=DifyConfig(enabled=False))
    outcome = runner.invoke("客服电话多少")
    assert outcome.dify_trace == ()
    assert "关闭" in outcome.reply


def test_dify_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_dify_config(DifyConfig(workflow_name="custom-workflow", max_nodes=5))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_dify_config()
    assert cfg.workflow_name == "custom-workflow"
    assert cfg.max_nodes == 5
