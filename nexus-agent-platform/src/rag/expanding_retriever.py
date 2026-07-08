"""
Expanding 检索管线 — 多 query 扩展 → inner 检索 → 合并去重

需求：ZL-NA-REQ-035
"""

from __future__ import annotations

from rag.expansion_config import ExpansionConfig
from rag.query_expander import ExpansionResult, QueryExpander, build_expander
from rag.query_rewriter import RewriteResult
from rag.result_merger import merge_retrieval_results
from rag.rewriting_retriever import RewritingRetriever
from rag.retriever import RetrievalResult


class ExpandingRetriever:
    """
    最外层检索装饰器 — 扩展 query 后多路检索并合并

    典型用法：
        inner = RewritingRetriever(RerankingRetriever(...))
        retriever = ExpandingRetriever(inner, config=ExpansionConfig())
        hits = retriever.search("理财安全吗", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        expander: QueryExpander | None = None,
        config: ExpansionConfig | None = None,
    ) -> None:
        self._inner = inner
        self._config = config or ExpansionConfig()
        self._expander = expander or build_expander(self._config)
        self._last_expansion: ExpansionResult | None = None
        self._last_inner_rewrite: RewriteResult | None = None

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> ExpansionConfig:
        return self._config

    @property
    def last_expansion(self) -> ExpansionResult | None:
        """最近一次 search 的扩展结果（演示 / 审计）"""
        return self._last_expansion

    @property
    def last_inner_rewrite(self) -> RewriteResult | None:
        """首条扩展 query 经 inner 改写后的审计结果"""
        return self._last_inner_rewrite

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            self._last_expansion = None
            self._last_inner_rewrite = None
            return []

        cfg = self._config
        if not cfg.enabled:
            self._last_expansion = ExpansionResult(
                original=query,
                queries=(query,),
                changed=False,
                mode=cfg.mode,
            )
            self._last_inner_rewrite = None
            if isinstance(self._inner, RewritingRetriever):
                self._inner.search(query, top_k=top_k)
                self._last_inner_rewrite = self._inner.last_rewrite
            return self._inner.search(query, top_k=top_k)

        expansion = self._expander.expand(query)
        self._last_expansion = expansion
        self._last_inner_rewrite = None
        queries = expansion.queries[: cfg.max_queries]
        if not queries:
            queries = (query,)

        per_k = max(top_k, cfg.per_query_top_k)
        batches: list[list[RetrievalResult]] = []
        for i, q in enumerate(queries):
            q = q.strip()
            if q:
                batch = self._inner.search(q, top_k=per_k)
                if i == 0 and isinstance(self._inner, RewritingRetriever):
                    self._last_inner_rewrite = self._inner.last_rewrite
                batches.append(batch)

        if not batches:
            return self._inner.search(query, top_k=top_k)

        return merge_retrieval_results(batches, top_k=top_k)
