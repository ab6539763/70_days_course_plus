"""
混合检索器 — 关键词 + 向量分数融合

将 KeywordRetriever（稀疏命中）与 ChromaEmbeddingRetriever（稠密相似度）
按加权或 RRF 合并，改善精确词与语义问句的召回平衡。

需求：ZL-NA-REQ-031
"""

from __future__ import annotations

from rag.chunker import TextChunk
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding_retriever import EmbeddingRetriever
from rag.retrieval_config import (
    FUSION_RRF,
    FUSION_WEIGHTED,
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)
from rag.retriever import KeywordRetriever, RetrievalResult


class HybridRetriever:
    """
    混合检索器 — 统一 search() 接口

    典型用法：
        cfg = RetrievalConfig(mode="hybrid", fusion="rrf")
        retriever = HybridRetriever(chunks, keyword, vector, config=cfg)
        hits = retriever.search("最低起购金额", top_k=3)
    """

    def __init__(
        self,
        chunks: list[TextChunk],
        keyword: KeywordRetriever,
        vector: ChromaEmbeddingRetriever | EmbeddingRetriever,
        *,
        config: RetrievalConfig | None = None,
    ) -> None:
        self._chunks = list(chunks)
        self._keyword = keyword
        self._vector = vector
        self._config = config or RetrievalConfig()

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks:
            return []

        cfg = self._config
        if cfg.mode == MODE_VECTOR:
            return self._vector.search(query, top_k=top_k)
        if cfg.mode == MODE_KEYWORD:
            return self._keyword.search(query, top_k=top_k)

        pool = max(top_k * 4, 8)
        kw_hits = self._keyword.search(query, top_k=pool)
        vec_hits = self._vector.search(query, top_k=pool)
        if cfg.fusion == FUSION_RRF:
            merged = _rrf_merge(kw_hits, vec_hits, rrf_k=cfg.rrf_k)
        else:
            merged = _weighted_merge(
                kw_hits,
                vec_hits,
                keyword_weight=cfg.keyword_weight,
                vector_weight=cfg.vector_weight,
            )
        return merged[: max(1, top_k)]


def _weighted_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    keyword_weight: float,
    vector_weight: float,
) -> list[RetrievalResult]:
    """按归一化分数加权求和"""
    kw_norm = _normalize_scores(kw_hits)
    vec_norm = _normalize_scores(vec_hits)
    by_id: dict[str, RetrievalResult] = {}

    for r in kw_hits:
        by_id[r.chunk.chunk_id] = r
    for r in vec_hits:
        by_id.setdefault(r.chunk.chunk_id, r)

    scored: list[RetrievalResult] = []
    for chunk_id, base in by_id.items():
        ks = kw_norm.get(chunk_id, 0.0)
        vs = vec_norm.get(chunk_id, 0.0)
        combined = keyword_weight * ks + vector_weight * vs
        if combined <= 0:
            continue
        matched = tuple(dict.fromkeys((*base.matched_tokens,)))
        scored.append(
            RetrievalResult(
                chunk=base.chunk,
                score=combined,
                matched_tokens=matched,
            )
        )
    scored.sort(key=lambda r: (-r.score, r.chunk.index))
    return scored


def _rrf_merge(
    kw_hits: list[RetrievalResult],
    vec_hits: list[RetrievalResult],
    *,
    rrf_k: int,
) -> list[RetrievalResult]:
    """Reciprocal Rank Fusion — 不依赖原始分数尺度"""
    scores: dict[str, float] = {}
    chunks: dict[str, TextChunk] = {}
    tokens: dict[str, tuple[str, ...]] = {}

    for rank, r in enumerate(kw_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        tokens[cid] = r.matched_tokens

    for rank, r in enumerate(vec_hits, start=1):
        cid = r.chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        chunks[cid] = r.chunk
        if r.matched_tokens:
            prev = tokens.get(cid, ())
            tokens[cid] = tuple(dict.fromkeys((*prev, *r.matched_tokens)))

    max_rrf = max(scores.values()) if scores else 1.0
    results = [
        RetrievalResult(
            chunk=chunks[cid],
            score=scores[cid] / max_rrf,
            matched_tokens=tokens.get(cid, ()),
        )
        for cid in scores
    ]
    results.sort(key=lambda r: (-r.score, r.chunk.index))
    return results


def _normalize_scores(hits: list[RetrievalResult]) -> dict[str, float]:
    if not hits:
        return {}
    max_s = max(r.score for r in hits) or 1.0
    return {r.chunk.chunk_id: r.score / max_s for r in hits}
