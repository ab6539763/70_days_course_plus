"""
向后兼容 — MessageHistory 已迁移至 services.message_history

新代码请使用：
    from services import MessageHistory
"""

from __future__ import annotations

from services.message_history import MessageHistory, MessageHistoryService

__all__ = ["MessageHistory", "MessageHistoryService"]
