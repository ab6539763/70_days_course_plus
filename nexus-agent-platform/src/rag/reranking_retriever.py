"""
Reranking 检索管线 — hybrid 宽召回 → cross-encoder 精排

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker, Reranker
from rag.retriever import RetrievalResult


class RerankingRetriever:
    """
    两阶段检索器 — 内层负责召回，外层 reranker 负责精排

    典型用法：
        inner = HybridRetriever(...)
        retriever = RerankingRetriever(inner, config=RerankConfig())
        hits = retriever.search("年化收益率", top_k=3)
    """

    def __init__(
        self,
        inner,
        *,
        reranker: Reranker | None = None,
        config: RerankConfig | None = None,
    ) -> None:
        self._inner = inner
        self._reranker = reranker or MockCrossEncoderReranker()
        self._config = config or RerankConfig()

    @property
    def inner(self):
        return self._inner

    @property
    def config(self) -> RerankConfig:
        return self._config

    @property
    def chunk_count(self) -> int:
        return getattr(self._inner, "chunk_count", 0)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query:
            return []

        cfg = self._config
        if not cfg.enabled:
            return self._inner.search(query, top_k=top_k)

        pool = max(cfg.candidate_pool, top_k)
        candidates = self._inner.search(query, top_k=pool)
        if not candidates:
            return []

        return self._reranker.rerank(query, candidates, top_k=top_k)
