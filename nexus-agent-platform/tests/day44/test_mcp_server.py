"""Day 44 MCP Server/Runner 单元测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.mcp_bridge import structured_tools_from_mcp
from agent.mcp_client import McpClient
from agent.mcp_config import McpConfig
from agent.mcp_protocol import MCP_METHOD_CALL, MCP_METHOD_LIST, McpJsonRpcRequest
from agent.mcp_runner import McpRunner
from agent.mcp_server import NexusMcpServer
from api.factory import create_orchestrator


@pytest.fixture
def runner():
    orch = create_orchestrator()
    return McpRunner.from_executor(orch.tool_executor, config=McpConfig())


def test_mcp_config_validate():
    McpConfig().validate()
    with pytest.raises(ValueError):
        McpConfig(max_tool_calls=0).validate()
    with pytest.raises(ValueError):
        McpConfig(server_name="  ").validate()


def test_mcp_server_list_tools(runner):
    server = runner._server  # noqa: SLF001
    tools = server.list_tools()
    names = {t.name for t in tools}
    assert "faq_lookup" in names
    assert "rag_search" in names


def test_mcp_server_handle_list(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(McpJsonRpcRequest(method=MCP_METHOD_LIST))
    assert resp.ok
    assert len(resp.result["tools"]) >= 3


def test_mcp_server_handle_call_faq(runner):
    server = runner._server  # noqa: SLF001
    resp = server.handle(
        McpJsonRpcRequest(
            method=MCP_METHOD_CALL,
            params={"name": "faq_lookup", "arguments": {"query": "客服电话"}},
        )
    )
    assert resp.ok
    text = resp.result["content"][0]["text"]
    assert text


def test_mcp_client_list_and_call(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    tools = client.list_tools()
    assert any(t.name == "rag_search" for t in tools)
    obs = client.call_tool("rag_search", {"query": "年化收益"})
    assert obs


def test_mcp_bridge_structured_tools(runner):
    client = McpClient(runner._server)  # noqa: SLF001
    structured = structured_tools_from_mcp(client)
    names = {t.name for t in structured}
    assert "intent_classify" in names
    out = structured[0].run({"query": "测试"})
    assert isinstance(out, str)


def test_mcp_runner_faq_delegation(runner):
    outcome = runner.invoke("客服电话多少")
    assert "faq_lookup" in outcome.tools_used
    assert "faq_lookup" in outcome.mcp_tools
    assert any(s.phase == "call" for s in outcome.steps)


def test_mcp_runner_rag_delegation(runner):
    outcome = runner.invoke("年化收益怎么样")
    assert "rag_search" in outcome.tools_used


def test_mcp_runner_intent_delegation(runner):
    outcome = runner.invoke("帮我总结一下理财产品")
    assert "intent_classify" in outcome.tools_used


def test_mcp_config_persists_in_store(tmp_path):
    from rag.knowledge_store import KnowledgeStore

    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.set_mcp_config(McpConfig(server_name="custom-mcp", max_tool_calls=3))
    store.save(path)
    loaded = KnowledgeStore.load(path)
    cfg = loaded.get_mcp_config()
    assert cfg.server_name == "custom-mcp"
    assert cfg.max_tool_calls == 3
