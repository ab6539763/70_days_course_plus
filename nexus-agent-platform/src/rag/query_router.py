"""
检索管线查询路由 — 意图分类 + expand/rewrite 开关

与 Day18 IntentRouter（Prompt 模板）正交：本模块决定**检索子管线**走哪条分支。

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.route_config import (
    INTENT_FAQ_FAST,
    INTENT_RAG_STANDARD,
    INTENT_RAG_WIDE,
    RouteConfig,
)

# (rule_id, pattern, intent, expand, rewrite)
DEFAULT_ROUTE_RULES: tuple[tuple[str, str, str, bool, bool], ...] = (
    (
        "faq_phone",
        r"电话|客服|联系|400-|热线",
        INTENT_FAQ_FAST,
        False,
        False,
    ),
    (
        "faq_upload",
        r"上传|pdf|文档怎么",
        INTENT_FAQ_FAST,
        False,
        True,
    ),
    (
        "wide_safety",
        r"安全吗|会不会亏|保本|合规",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "wide_risk",
        r"有风险吗|风险大吗|谨慎",
        INTENT_RAG_WIDE,
        True,
        True,
    ),
    (
        "standard_yield",
        r"年化|收益|赚多少|利率",
        INTENT_RAG_STANDARD,
        False,
        True,
    ),
)

INTENT_LABELS: dict[str, str] = {
    INTENT_FAQ_FAST: "FAQ 快路径 — 跳过 expand/rewrite",
    INTENT_RAG_STANDARD: "标准 RAG — rewrite，不 expand",
    INTENT_RAG_WIDE: "宽召回 — expand + rewrite",
}


@dataclass(frozen=True)
class RouteResult:
    """单条路由结果 — 供审计与 preview API"""

    original: str
    intent: str
    expand: bool
    rewrite: bool
    rule_id: str | None = None
    confidence: float = 0.0
    label: str = ""

    def to_dict(self) -> dict[str, str | bool | float | None]:
        return {
            "original": self.original,
            "intent": self.intent,
            "expand": self.expand,
            "rewrite": self.rewrite,
            "rule_id": self.rule_id,
            "confidence": round(self.confidence, 4),
            "label": self.label or INTENT_LABELS.get(self.intent, self.intent),
        }


class QueryRouter(ABC):
    """查询路由器抽象接口"""

    @abstractmethod
    def route(self, query: str) -> RouteResult:
        """将用户问句路由到检索子管线"""


class RuleBasedQueryRouter(QueryRouter):
    """
    规则表路由器 — 可审计、无 LLM 依赖

    命中第一条 regex 规则即返回对应 expand/rewrite 开关。
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str, bool, bool], ...] | None = None,
        config: RouteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ROUTE_RULES
        self._config = config or RouteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), intent, expand, rewrite)
            for rid, pat, intent, expand, rewrite in self._rules
        ]

    @property
    def config(self) -> RouteConfig:
        return self._config

    def route(self, query: str) -> RouteResult:
        original = (query or "").strip()
        if not original:
            return self._fallback("")

        for rid, pattern, intent, expand, rewrite in self._compiled:
            if pattern.search(original):
                return RouteResult(
                    original=original,
                    intent=intent,
                    expand=expand,
                    rewrite=rewrite,
                    rule_id=rid,
                    confidence=0.9,
                    label=INTENT_LABELS.get(intent, intent),
                )

        return self._fallback(original)

    def _fallback(self, original: str) -> RouteResult:
        intent = self._config.fallback_intent
        expand = intent == INTENT_RAG_WIDE
        rewrite = intent != INTENT_FAQ_FAST
        return RouteResult(
            original=original,
            intent=intent,
            expand=expand,
            rewrite=rewrite,
            rule_id=None,
            confidence=0.6,
            label=INTENT_LABELS.get(intent, intent),
        )
