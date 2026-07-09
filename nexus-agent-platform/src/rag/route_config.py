"""
检索管线路由配置 — 按意图动态开关 expand / rewrite

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODE_RULES = "rules"

INTENT_FAQ_FAST = "faq_fast"
INTENT_RAG_STANDARD = "rag_standard"
INTENT_RAG_WIDE = "rag_wide"


@dataclass
class RouteConfig:
    """RAG 检索管线路由策略"""

    enabled: bool = True
    mode: str = MODE_RULES
    fallback_intent: str = INTENT_RAG_STANDARD

    def validate(self) -> None:
        if self.mode not in (MODE_RULES,):
            raise ValueError(f"mode 须为 rules，收到 {self.mode!r}")
        valid = {INTENT_FAQ_FAST, INTENT_RAG_STANDARD, INTENT_RAG_WIDE}
        if self.fallback_intent not in valid:
            raise ValueError(f"fallback_intent 无效: {self.fallback_intent!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "fallback_intent": self.fallback_intent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RouteConfig:
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            mode=str(data.get("mode", MODE_RULES)),
            fallback_intent=str(data.get("fallback_intent", INTENT_RAG_STANDARD)),
        )
