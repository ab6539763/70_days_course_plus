"""
多路检索结果合并 — 按 chunk_id 去重，保留最高分

需求：ZL-NA-REQ-035
"""

from __future__ import annotations

from rag.retriever import RetrievalResult


def merge_retrieval_results(
    batches: list[list[RetrievalResult]],
    *,
    top_k: int = 3,
) -> list[RetrievalResult]:
    """
    合并多路检索结果。

    - 同一 chunk_id 仅保留 score 最高的一条
    - 按 score 降序、chunk.index 升序排序
    """
    if top_k < 1:
        return []

    best: dict[str, RetrievalResult] = {}
    for batch in batches:
        for result in batch:
            cid = result.chunk.chunk_id
            prev = best.get(cid)
            if prev is None or result.score > prev.score:
                best[cid] = result

    merged = sorted(
        best.values(),
        key=lambda r: (-r.score, r.chunk.index),
    )
    return merged[:top_k]
