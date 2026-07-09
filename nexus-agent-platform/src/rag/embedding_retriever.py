"""
向量检索器 — 基于 Embedding 余弦相似度

与 KeywordRetriever 接口一致，可注入 DocumentIndex.retriever。

需求：ZL-NA-REQ-020
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.chunker import TextChunk
from rag.embedding import EmbeddingClient, EmbeddingVector, TfidfEmbeddingModel
from rag.retriever import RetrievalResult


@dataclass
class IndexedChunk:
    """带向量的文本块"""

    chunk: TextChunk
    vector: EmbeddingVector


class EmbeddingRetriever:
    """Embedding 向量检索器"""

    def __init__(
        self,
        chunks: list[TextChunk] | None = None,
        *,
        client: EmbeddingClient | None = None,
        min_score: float = 0.05,
    ) -> None:
        self._client = client or EmbeddingClient()
        self._indexed: list[IndexedChunk] = []
        self._min_score = min_score
        if chunks:
            self.index(chunks)

    @property
    def chunk_count(self) -> int:
        return len(self._indexed)

    def index(self, chunks: list[TextChunk]) -> None:
        """在文本块上训练 TF-IDF 并预计算向量"""
        texts = [c.text for c in chunks]
        self._client.fit_corpus(texts)
        vectors = self._client.embed_batch(texts)
        self._indexed = [
            IndexedChunk(chunk=chunk, vector=vec)
            for chunk, vec in zip(chunks, vectors)
        ]

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._indexed:
            return []

        query_vec = self._client.embed(query)
        scored: list[RetrievalResult] = []

        for item in self._indexed:
            score = query_vec.similarity_to(item.vector)
            if score >= self._min_score:
                matched = _overlap_terms(query, item.chunk.text)
                scored.append(
                    RetrievalResult(
                        chunk=item.chunk,
                        score=score,
                        matched_tokens=matched,
                    )
                )

        scored.sort(key=lambda r: (-r.score, r.chunk.index))
        if not scored:
            return []
        return scored[: max(1, top_k)]


def _overlap_terms(query: str, text: str, limit: int = 5) -> tuple[str, ...]:
    """提取查询与文档共现词（可解释性）"""
    from rag.synonyms import expand_tokens, tokenize

    q_set = set(expand_tokens(tokenize(query), query))
    t_set = set(expand_tokens(tokenize(text), text))
    common = [t for t in q_set if t in t_set]
    return tuple(common[:limit])
