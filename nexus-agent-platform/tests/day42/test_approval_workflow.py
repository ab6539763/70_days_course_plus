"""Day 42 ApprovalWorkflowGraph 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import GraphConfig
from api.factory import create_orchestrator


@pytest.fixture(autouse=True)
def clear_checkpoints():
    approval_checkpoint_store.clear()
    yield
    approval_checkpoint_store.clear()


@pytest.fixture
def workflow():
    orch = create_orchestrator()
    return ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        graph_config=GraphConfig(max_iterations=4),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )


def test_approval_config_validate():
    ApprovalConfig().validate()
    with pytest.raises(ValueError):
        ApprovalConfig(reviewer_label="").validate()


def test_faq_skips_approval_node(workflow):
    outcome = workflow.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "human_approval" not in outcome.node_path
    assert outcome.approval_status in ("skipped", "approved")


def test_rag_with_mock_auto_approve(workflow):
    outcome = workflow.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert "human_approval" in outcome.node_path
    assert outcome.approval_status == "approved"
    assert not outcome.interrupted


def test_interrupt_and_resume_approve():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    assert pending.interrupted
    assert pending.checkpoint_id
    assert pending.approval_status == "pending"

    resumed = flow.resume(pending.checkpoint_id, approved=True, comment="OK")
    assert resumed.approval_status == "approved"
    assert resumed.reply
    assert not resumed.interrupted


def test_interrupt_and_resume_reject():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(
        orch.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = flow.invoke("年化收益怎么样")
    resumed = flow.resume(pending.checkpoint_id, approved=False)
    assert resumed.approval_status == "rejected"
    assert "未通过" in resumed.reply or "审批" in resumed.reply


def test_approval_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_approval_config(
        ApprovalConfig(mock_auto_approve=False, reviewer_label="风控专员")
    )
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_approval_config()
    assert cfg.mock_auto_approve is False
    assert cfg.reviewer_label == "风控专员"


def test_resume_unknown_checkpoint():
    orch = create_orchestrator()
    flow = ApprovalWorkflowGraph.from_executor(orch.tool_executor)
    outcome = flow.resume("missing-id", approved=True)
    assert outcome.approval_status == "error"
