"""
知识库增量索引 — 单文档 upsert 与替换

Day 30：upload 路径不再全量 reset Chroma，仅 upsert 受影响 chunk。

需求：ZL-NA-REQ-030
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.knowledge_store import KnowledgeStore


@dataclass
class IncrementalReport:
    """单次增量索引报告"""

    filename: str
    chunks_added: int
    chunks_removed: int
    vocab_expanded: bool
    chroma_count: int
    incremental_at: str
    index_mode: str = "incremental"

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "chunks_added": self.chunks_added,
            "chunks_removed": self.chunks_removed,
            "vocab_expanded": self.vocab_expanded,
            "chroma_count": self.chroma_count,
            "incremental_at": self.incremental_at,
            "index_mode": self.index_mode,
        }


def incremental_upload(
    store: KnowledgeStore,
    *,
    filename: str,
    chunks_removed: int,
    chunks_added: int,
    vocab_expanded: bool,
) -> IncrementalReport:
    """构建增量索引报告（供 API / demo 使用）"""
    return IncrementalReport(
        filename=filename,
        chunks_added=chunks_added,
        chunks_removed=chunks_removed,
        vocab_expanded=vocab_expanded,
        chroma_count=store._chroma_index().count(),
        incremental_at=store.last_incremental_at or "",
    )
