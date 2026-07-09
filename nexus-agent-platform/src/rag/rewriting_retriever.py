"""
Rewriting 检索管线 — 查询改写 → hybrid → rerank

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

from rag.query_rewriter import QueryRewriter, RewriteResult, RuleBasedQueryRewriter
from rag.rewrite_config import RewriteConfig
from rag.retriever import RetrievalResult


class RewritingRetriever:
    """
    最外层检索装饰器 — 先改写 query，再委托内层检索

    典型用法：
        inner = RerankingRetriever(HybridRetriever(...))
        retriever = RewritingRetriever(inner, config=RewriteConfig())
        hits = retriever.search("那个理财能赚多少", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        rewriter: QueryRewriter | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._inner = inner
        self._config = config or RewriteConfig()
        self._rewriter = rewriter or RuleBasedQueryRewriter(config=self._config)
        self._last_rewrite: RewriteResult | None = None

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RewriteConfig:
        return self._config

    @property
    def last_rewrite(self) -> RewriteResult | None:
        """最近一次 search 的改写结果（演示 / 审计）"""
        return self._last_rewrite

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        rewrite_override: bool | None = None,
    ) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_rewrite = None
            return []

        cfg = self._config
        enabled = rewrite_override if rewrite_override is not None else cfg.enabled
        if not enabled:
            self._last_rewrite = RewriteResult(
                original=query, rewritten=query, changed=False
            )
            return self._inner.search(query, top_k=top_k)

        result = self._rewriter.rewrite(query)
        self._last_rewrite = result
        search_q = result.rewritten or query
        return self._inner.search(search_q, top_k=top_k)
