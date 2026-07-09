"""
Routing 检索管线 — 意图路由 → 动态 expand/rewrite → inner 检索

需求：ZL-NA-REQ-036
"""

from __future__ import annotations

from rag.query_router import QueryRouter, RouteResult, RuleBasedQueryRouter
from rag.route_config import INTENT_FAQ_FAST, INTENT_RAG_STANDARD, INTENT_RAG_WIDE, RouteConfig
from rag.retriever import RetrievalResult


class RoutingRetriever:
    """
    最外层检索装饰器 — 按意图动态开关 expand / rewrite

    典型用法：
        inner = ExpandingRetriever(RewritingRetriever(...))
        retriever = RoutingRetriever(inner, config=RouteConfig())
        hits = retriever.search("客服电话多少", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        router: QueryRouter | None = None,
        config: RouteConfig | None = None,
    ) -> None:
        self._inner = inner
        self._config = config or RouteConfig()
        self._router = router or RuleBasedQueryRouter(config=self._config)
        self._last_route: RouteResult | None = None

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RouteConfig:
        return self._config

    @property
    def last_route(self) -> RouteResult | None:
        """最近一次 search 的路由结果（演示 / 审计）"""
        return self._last_route

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3, intent_override: str | None = None) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_route = None
            return []

        if not self._config.enabled:
            self._last_route = RouteResult(
                original=query,
                intent=self._config.fallback_intent,
                expand=True,
                rewrite=True,
                confidence=0.5,
            )
            return self._inner.search(query, top_k=top_k)

        if intent_override:
            route = _route_from_intent(query, intent_override)
        else:
            route = self._router.route(query)
        self._last_route = route
        return self._inner.search(
            query,
            top_k=top_k,
            expand_override=route.expand,
            rewrite_override=route.rewrite,
        )


def _route_from_intent(query: str, intent: str) -> RouteResult:
    """强制意图路由 — 供 Self-RAG 重试宽召回使用"""
    from rag.query_router import INTENT_LABELS

    expand = intent == INTENT_RAG_WIDE
    rewrite = intent != INTENT_FAQ_FAST
    if intent == INTENT_RAG_STANDARD:
        expand, rewrite = False, True
    elif intent == INTENT_RAG_WIDE:
        expand, rewrite = True, True
    elif intent == INTENT_FAQ_FAST:
        expand, rewrite = False, False
    return RouteResult(
        original=query,
        intent=intent,
        expand=expand,
        rewrite=rewrite,
        rule_id="retry_override",
        confidence=1.0,
        label=INTENT_LABELS.get(intent, intent),
    )
