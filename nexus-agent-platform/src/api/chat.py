"""
Chat REST API 路由

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.response_parser import classify_reply
from api.schemas import ChatRequest, ChatResponse, HealthResponse, SessionResetRequest, SessionResetResponse
from api.sessions import SessionManager, session_manager
from chat.orchestrator import ChatOrchestrator
from core.exceptions import APIError, ConfigError, NexusError

API_VERSION = "0.28.0"

router = APIRouter(prefix="/api", tags=["chat"])


def get_session_manager() -> SessionManager:
    return session_manager


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
    处理单轮聊天请求，内部调用 ChatOrchestrator.handle_message。
    """
    session_id, orchestrator = manager.get_or_create(body.session_id)
    message = body.message.strip()

    try:
        reply = orchestrator.handle_message(message)
    except ConfigError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc
    except APIError as exc:
        raise _http_from_nexus(exc, status_code=502) from exc
    except NexusError as exc:
        raise _http_from_nexus(exc, status_code=500) from exc

    kind, meta = classify_reply(reply)
    return ChatResponse(
        reply=reply,
        meta=meta,
        kind=kind,
        session_id=session_id,
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
