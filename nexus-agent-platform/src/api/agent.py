"""
ReAct / AgentExecutor / StateGraph REST API — 配置与 preview

需求：ZL-NA-REQ-039 / ZL-NA-REQ-040 / ZL-NA-REQ-041
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.agent_executor import AgentExecutor
from agent.executor_config import ExecutorConfig
from agent.graph_config import GraphConfig
from agent.rag_agent_graph import RAGAgentGraph
from agent.react_agent import ReActAgent
from agent.react_config import ReactConfig
from api.factory import create_orchestrator
from api.schemas import (
    ExecutorConfigRequest,
    ExecutorConfigResponse,
    ExecutorPreviewRequest,
    ExecutorPreviewResponse,
    GraphConfigRequest,
    GraphConfigResponse,
    GraphPreviewRequest,
    GraphPreviewResponse,
    ReactConfigRequest,
    ReactConfigResponse,
    ReactPreviewRequest,
    ReactPreviewResponse,
)
from rag.knowledge_store import get_knowledge_store

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/react-config", response_model=ReactConfigResponse)
def get_react_config() -> ReactConfigResponse:
    cfg = get_knowledge_store().get_react_config()
    return ReactConfigResponse(**cfg.to_dict())


@router.put("/react-config", response_model=ReactConfigResponse)
def update_react_config(body: ReactConfigRequest) -> ReactConfigResponse:
    store = get_knowledge_store()
    try:
        cfg = ReactConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_react_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReactConfigResponse(**cfg.to_dict())


@router.post("/react-preview", response_model=ReactPreviewResponse)
def react_preview(body: ReactPreviewRequest) -> ReactPreviewResponse:
    """无状态 ReAct 运行 — 返回完整 agent_trace"""
    store = get_knowledge_store()
    cfg = store.get_react_config()
    if not cfg.enabled:
        raise HTTPException(status_code=400, detail="ReAct Agent 已关闭")

    orchestrator = create_orchestrator()
    agent = ReActAgent(orchestrator.tool_executor, config=cfg)
    history = [{"role": "user", "content": h} for h in (body.history or [])]
    outcome = agent.run(body.query, history=history or None)
    payload = outcome.to_dict()
    return ReactPreviewResponse(**payload)


@router.get("/executor-config", response_model=ExecutorConfigResponse)
def get_executor_config() -> ExecutorConfigResponse:
    cfg = get_knowledge_store().get_executor_config()
    return ExecutorConfigResponse(**cfg.to_dict())


@router.put("/executor-config", response_model=ExecutorConfigResponse)
def update_executor_config(body: ExecutorConfigRequest) -> ExecutorConfigResponse:
    store = get_knowledge_store()
    try:
        cfg = ExecutorConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_executor_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExecutorConfigResponse(**cfg.to_dict())


@router.post("/executor-preview", response_model=ExecutorPreviewResponse)
def executor_preview(body: ExecutorPreviewRequest) -> ExecutorPreviewResponse:
    """无状态 AgentExecutor 运行 — 返回 executor_trace 对齐字段"""
    store = get_knowledge_store()
    cfg = store.get_executor_config()
    if not cfg.enabled:
        raise HTTPException(status_code=400, detail="AgentExecutor 已关闭")

    orchestrator = create_orchestrator()
    agent = AgentExecutor.from_executor(orchestrator.tool_executor, config=cfg)
    history = [{"role": "user", "content": h} for h in (body.history or [])]
    outcome = agent.invoke(body.query, history=history or None)
    payload = outcome.to_dict()
    return ExecutorPreviewResponse(**payload)


@router.get("/graph-config", response_model=GraphConfigResponse)
def get_graph_config() -> GraphConfigResponse:
    cfg = get_knowledge_store().get_graph_config()
    return GraphConfigResponse(**cfg.to_dict())


@router.put("/graph-config", response_model=GraphConfigResponse)
def update_graph_config(body: GraphConfigRequest) -> GraphConfigResponse:
    store = get_knowledge_store()
    try:
        cfg = GraphConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_graph_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GraphConfigResponse(**cfg.to_dict())


@router.post("/graph-preview", response_model=GraphPreviewResponse)
def graph_preview(body: GraphPreviewRequest) -> GraphPreviewResponse:
    """无状态 StateGraph 运行 — 返回 graph_trace 与 node_path"""
    store = get_knowledge_store()
    cfg = store.get_graph_config()
    if not cfg.enabled:
        raise HTTPException(status_code=400, detail="StateGraph 已关闭")

    orchestrator = create_orchestrator()
    graph = RAGAgentGraph.from_executor(orchestrator.tool_executor, config=cfg)
    history = [{"role": "user", "content": h} for h in (body.history or [])]
    outcome = graph.invoke(body.query, history=history or None)
    payload = outcome.to_dict()
    return GraphPreviewResponse(**payload)
