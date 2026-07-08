"""
引用溯源构建 — 检索结果 → 结构化 citations

将 RetrievalResult 列表转为可审计、可展示的引用条目，
并可选附带 Day33 rewrite 元数据。

需求：ZL-NA-REQ-034
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.citation_config import CitationConfig
from rag.query_rewriter import RewriteResult
from rag.retriever import RetrievalResult


@dataclass(frozen=True)
class Citation:
    """单条可引用片段"""

    rank: int
    chunk_id: str
    source: str
    score: float
    preview: str
    matched_tokens: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "chunk_id": self.chunk_id,
            "source": self.source,
            "score": round(self.score, 4),
            "preview": self.preview,
            "matched_tokens": list(self.matched_tokens),
        }


@dataclass(frozen=True)
class CitationBundle:
    """检索引用包 — citations + 可选 rewrite 审计"""

    citations: list[Citation]
    rewrite: RewriteResult | None = None
    query: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "query": self.query,
            "citations": [c.to_dict() for c in self.citations],
        }
        if self.rewrite is not None:
            data["rewrite"] = self.rewrite.to_dict()
        return data


def build_citations(
    results: list[RetrievalResult],
    *,
    preview_max_chars: int = 120,
    max_items: int = 3,
) -> list[Citation]:
    """将检索结果转为引用列表"""
    citations: list[Citation] = []
    for rank, result in enumerate(results[: max(1, max_items)], start=1):
        text = result.chunk.text.replace("\n", " ").strip()
        if len(text) > preview_max_chars:
            text = text[: preview_max_chars - 3] + "..."
        citations.append(
            Citation(
                rank=rank,
                chunk_id=result.chunk.chunk_id,
                source=result.chunk.source,
                score=result.score,
                preview=text,
                matched_tokens=result.matched_tokens,
            )
        )
    return citations


def build_citation_bundle(
    query: str,
    results: list[RetrievalResult],
    *,
    config: CitationConfig | None = None,
    rewrite: RewriteResult | None = None,
) -> CitationBundle:
    """组装完整引用包"""
    cfg = config or CitationConfig()
    citations = build_citations(
        results,
        preview_max_chars=cfg.preview_max_chars,
        max_items=cfg.max_citations,
    )
    rewrite_meta = rewrite if cfg.include_rewrite_meta else None
    return CitationBundle(
        citations=citations,
        rewrite=rewrite_meta,
        query=query.strip(),
    )
