"""
Chat REST API 路由

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from agent.agent_executor import AgentExecutor
from agent.react_agent import ReActAgent
from api.response_parser import classify_reply
from api.schemas import ChatRequest, ChatResponse, HealthResponse, SessionResetRequest, SessionResetResponse
from api.sessions import SessionManager, session_manager
from rag.knowledge_store import get_knowledge_store
from rag.validation_retry import apply_validation_retry
from core.exceptions import APIError, ConfigError, NexusError

API_VERSION = "0.40.0"

router = APIRouter(prefix="/api", tags=["chat"])


def get_session_manager() -> SessionManager:
    return session_manager


def _session_history(orchestrator, *, enabled: bool) -> list[dict[str, str]] | None:
    if not enabled:
        return None
    msgs = orchestrator.assistant.history.messages
    return [{"role": m.role, "content": m.content} for m in msgs if m.role in ("user", "assistant")]


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    import os

    return HealthResponse(
        status="ok",
        version=API_VERSION,
        mock_llm=os.environ.get("NEXUS_LLM_MOCK", "0") == "1",
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> ChatResponse:
    """
    处理单轮聊天请求；agent_mode=true 走 ReAct，executor_mode=true 走 AgentExecutor。
    """
    session_id, orchestrator = manager.get_or_create(body.session_id)
    message = body.message.strip()
    store = get_knowledge_store()
    agent_trace = None
    executor_trace = None
    tools_used = None

    try:
        if body.executor_mode and store.get_executor_config().enabled:
            cfg = store.get_executor_config()
            agent = AgentExecutor.from_executor(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            exec_outcome = agent.invoke(message, history=history)
            reply = exec_outcome.reply
            executor_trace = [s.to_dict() for s in exec_outcome.steps]
            tools_used = list(exec_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        elif body.agent_mode and store.get_react_config().enabled:
            cfg = store.get_react_config()
            agent = ReActAgent(orchestrator.tool_executor, config=cfg)
            history = _session_history(orchestrator, enabled=cfg.use_session_history)
            react_outcome = agent.run(message, history=history)
            reply = react_outcome.reply
            agent_trace = [s.to_dict() for s in react_outcome.steps]
            tools_used = list(react_outcome.tools_used)
            orchestrator.assistant.history.add_user(message)
            orchestrator.assistant.history.add_assistant(reply)
        else:
            reply = orchestrator.handle_message(message)
    except ConfigError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc
    except APIError as exc:
        raise _http_from_nexus(exc, status_code=502) from exc
    except NexusError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc

    kind, meta = classify_reply(reply)
    if executor_trace:
        kind = "executor"
        meta = "AgentExecutor"
    elif agent_trace:
        kind = "agent"
        meta = "ReAct Agent"

    cite_data = store.fetch_citations(message)
    citations = cite_data.get("citations") or []
    rewrite = cite_data.get("rewrite")
    expansion = cite_data.get("expansion")
    route = cite_data.get("route")

    validation = None
    outcome = apply_validation_retry(
        store,
        message,
        reply,
        citations,
        cite_data,
        regenerate_fn=lambda: orchestrator.handle_message(message),
    )
    if outcome is not None:
        reply = outcome.reply
        kind, meta = classify_reply(reply)
        if executor_trace:
            kind = "executor"
            meta = "AgentExecutor"
        elif agent_trace:
            kind = "agent"
            meta = "ReAct Agent"
        citations = outcome.citations
        cite_data = outcome.cite_data
        rewrite = cite_data.get("rewrite")
        expansion = cite_data.get("expansion")
        route = cite_data.get("route")
        validation = outcome.validation.to_dict()
        if outcome.refused:
            validation = {**validation, "refused": True}
        if outcome.validation.retries:
            validation = {
                **validation,
                "retry_route": cite_data.get("route"),
            }

    return ChatResponse(
        reply=reply,
        meta=meta,
        kind=kind,
        session_id=session_id,
        citations=citations,
        rewrite=rewrite,
        expansion=expansion,
        route=route,
        validation=validation,
        agent_trace=agent_trace,
        executor_trace=executor_trace,
        tools_used=tools_used,
    )


@router.post("/session/reset", response_model=SessionResetResponse)
def reset_session(
    body: SessionResetRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionResetResponse:
    """清除服务端会话编排器（新对话时调用）"""
    cleared = manager.clear(body.session_id)
    return SessionResetResponse(session_id=body.session_id, cleared=cleared)


def _http_from_nexus(exc: NexusError, *, status_code: int):
    from fastapi import HTTPException

    return HTTPException(
        status_code=status_code,
        detail={"detail": exc.message, "code": exc.code},
    )
