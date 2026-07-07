"""
API 会话管理 — 每会话独立 ChatOrchestrator

避免多用户共用一个 MessageHistory 导致串话。

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

import uuid
from threading import Lock

from chat.orchestrator import ChatOrchestrator

from api.factory import create_orchestrator


class SessionManager:
    """内存会话存储（教学 MVP，生产应换 Redis/DB）"""

    def __init__(self) -> None:
        self._sessions: dict[str, ChatOrchestrator] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str | None) -> tuple[str, ChatOrchestrator]:
        sid = (session_id or "").strip() or "default"
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = create_orchestrator()
            return sid, self._sessions[sid]

    def clear(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def count(self) -> int:
        return len(self._sessions)


# 全局单例（FastAPI 依赖注入使用）
session_manager = SessionManager()
