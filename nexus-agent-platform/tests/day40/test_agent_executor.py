"""Day 40 StructuredTool + AgentExecutor 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.agent_executor import AgentExecutor
from agent.executor_config import ExecutorConfig
from agent.structured_tool import StructuredTool, tool, tools_to_openai_schema
from agent.tool_adapter import tools_from_executor
from api.factory import create_orchestrator


@tool(name="add_nums", description="两数相加")
def add_nums(a: int, b: int) -> str:
    return str(a + b)


@pytest.fixture
def executor():
    orch = create_orchestrator()
    return AgentExecutor.from_executor(
        orch.tool_executor,
        config=ExecutorConfig(max_iterations=4),
    )


def test_executor_config_validate():
    ExecutorConfig().validate()
    with pytest.raises(ValueError):
        ExecutorConfig(max_iterations=0).validate()


def test_tool_decorator_and_schema():
    assert isinstance(add_nums, StructuredTool)
    assert add_nums.run({"a": 2, "b": 3}) == "5"
    schema = add_nums.to_openai_tool()
    assert schema["function"]["name"] == "add_nums"
    assert schema["function"]["parameters"]["properties"]["a"]["type"] == "integer"


def test_tools_from_executor():
    orch = create_orchestrator()
    tools = tools_from_executor(orch.tool_executor)
    names = {t.name for t in tools}
    assert "faq_lookup" in names
    assert "rag_search" in names
    openai = tools_to_openai_schema(tools)
    assert all(item["type"] == "function" for item in openai)


def test_executor_faq_lookup(executor):
    outcome = executor.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert outcome.reply
    assert len(outcome.steps) >= 2
    assert outcome.intermediate_steps


def test_executor_rag_search(executor):
    outcome = executor.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used
    assert outcome.reply


def test_executor_respects_max_iterations():
    orch = create_orchestrator()
    agent = AgentExecutor.from_executor(
        orch.tool_executor,
        config=ExecutorConfig(max_iterations=1),
    )
    outcome = agent.invoke("年化收益怎么样")
    assert len([s for s in outcome.steps if s.action]) <= 1


def test_executor_uses_history(executor):
    history = [{"role": "user", "content": "之前问过理财产品"}]
    outcome = executor.invoke("再查一下年化收益", history=history)
    assert outcome.reply
    assert any("会话记忆" in (s.thought or "") for s in outcome.steps)


def test_executor_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_executor_config(ExecutorConfig(max_iterations=5, mock_planner=True))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_executor_config()
    assert cfg.max_iterations == 5
