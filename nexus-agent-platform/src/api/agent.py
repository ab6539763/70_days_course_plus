"""
ReAct Agent REST API — 配置与 preview

需求：ZL-NA-REQ-039
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.react_agent import ReActAgent
from agent.react_config import ReactConfig
from api.factory import create_orchestrator
from api.schemas import (
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
