"""
Chroma 向量检索器 — 与 EmbeddingRetriever 接口一致

需求：ZL-NA-REQ-029
"""

from __future__ import annotations

from rag.chunker import TextChunk
from rag.chroma_store import ChromaVectorIndex
from rag.embedding import EmbeddingClient
from rag.embedding_retriever import _overlap_terms
from rag.retriever import RetrievalResult


class ChromaEmbeddingRetriever:
    """基于 Chroma 持久化索引的向量检索器"""

    def __init__(
        self,
        chunks: list[TextChunk],
        chroma_index: ChromaVectorIndex,
        *,
        client: EmbeddingClient | None = None,
        min_score: float = 0.05,
    ) -> None:
        self._chunks_by_id = {c.chunk_id: c for c in chunks}
        self._chroma = chroma_index
        self._client = client or EmbeddingClient()
        self._min_score = min_score

    @property
    def chunk_count(self) -> int:
        return self._chroma.count()

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks_by_id:
            return []

        if not self._client.model.is_fitted:
            return []

        query_vec = self._client.embed(query)
        hits = self._chroma.query(
            query_vec.values,
            top_k=top_k,
            min_score=self._min_score,
        )

        scored: list[RetrievalResult] = []
        for hit in hits:
            chunk = self._chunks_by_id.get(hit.chunk_id)
            if chunk is None:
                continue
            matched = _overlap_terms(query, chunk.text)
            scored.append(
                RetrievalResult(
                    chunk=chunk,
                    score=hit.score,
                    matched_tokens=matched,
                )
            )

        if not scored:
            return []
        return scored[: max(1, top_k)]
