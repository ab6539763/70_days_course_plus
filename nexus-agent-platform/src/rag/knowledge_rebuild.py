"""
知识库全量重建 — 按当前 chunk_config 重扫源文件

需求：ZL-NA-REQ-028
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import get_path
from rag.chunk_config import ChunkConfig
from rag.chunk_strategies import chunk_from_parsed
from rag.knowledge_store import KnowledgeDocument, KnowledgeStore
from tools.doc_parser import SUPPORTED_EXTENSIONS, parse_bytes
from utils.text_utils import clean_text

_SOURCE_GLOBS = tuple(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))


@dataclass
class RebuildReport:
    """全量重建结果报告"""

    documents_before: int
    chunks_before: int
    documents_after: int
    chunks_after: int
    sources_processed: int
    chunk_config: ChunkConfig
    source_files: list[str] = field(default_factory=list)
    rebuilt_at: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents_before": self.documents_before,
            "chunks_before": self.chunks_before,
            "documents_after": self.documents_after,
            "chunks_after": self.chunks_after,
            "sources_processed": self.sources_processed,
            "chunk_config": self.chunk_config.to_dict(),
            "source_files": self.source_files,
            "rebuilt_at": self.rebuilt_at,
            "message": self.message,
        }


def collect_source_files(
    *,
    uploads_dir: Path | None = None,
    sample_docs_dir: Path | None = None,
    include_sample_docs: bool = True,
) -> list[Path]:
    """
    收集可重建的源文件。

    uploads 与 sample_docs 同名时，uploads 优先覆盖。
    """
    uploads = uploads_dir or get_path("knowledge_uploads")
    sample = sample_docs_dir or get_path("sample_docs")
    by_name: dict[str, Path] = {}

    if include_sample_docs and sample.is_dir():
        for pattern in _SOURCE_GLOBS:
            for path in sorted(sample.glob(pattern)):
                if path.is_file():
                    by_name[path.name] = path

    if uploads.is_dir():
        for pattern in _SOURCE_GLOBS:
            for path in sorted(uploads.glob(pattern)):
                if path.is_file():
                    by_name[path.name] = path

    return [by_name[name] for name in sorted(by_name)]


def rebuild_store(
    store: KnowledgeStore,
    *,
    include_sample_docs: bool = True,
    uploads_dir: Path | None = None,
    sample_docs_dir: Path | None = None,
) -> RebuildReport:
    """
    清空索引并按当前 chunk_config 从源文件全量重建。

    流程：收集源文件 → 清空 chunks/documents → 逐文件 parse+chunk → 重建 embedding → save
    """
    docs_before = store.document_count
    chunks_before = store.chunk_count
    cfg = store.get_chunk_config()

    sources = collect_source_files(
        uploads_dir=uploads_dir,
        sample_docs_dir=sample_docs_dir,
        include_sample_docs=include_sample_docs,
    )

    store.documents.clear()
    store.chunks.clear()
    store.invalidate_cache()

    for path in sources:
        parsed = parse_bytes(path.read_bytes(), path.name)
        text = parsed.plain_text.strip()
        if not text:
            continue
        text, _ = clean_text(text)
        parsed.plain_text = text
        for section in parsed.sections:
            section.body, _ = clean_text(section.body)

        new_chunks = chunk_from_parsed(
            parsed,
            strategy=cfg.strategy,
            chunk_size=cfg.chunk_size,
            overlap=cfg.overlap,
        )
        size_bytes = path.stat().st_size
        store._append_chunks(
            parsed.filename,
            new_chunks,
            size_bytes=size_bytes,
            doc_format=parsed.format,
        )

    store._rebuild_index()
    rebuilt_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    report = RebuildReport(
        documents_before=docs_before,
        chunks_before=chunks_before,
        documents_after=store.document_count,
        chunks_after=store.chunk_count,
        sources_processed=len(sources),
        chunk_config=cfg,
        source_files=[p.name for p in sources],
        rebuilt_at=rebuilt_at,
        message="知识库已按当前 chunk_config 全量重建",
    )
    store.last_rebuilt_at = rebuilt_at
    store.save()
    return report


def rebuild_with_best_config(
    store: KnowledgeStore,
    *,
    eval_sample_path: Path,
    include_sample_docs: bool = True,
) -> RebuildReport:
    """先运行 A/B 评估选最优配置，再全量重建"""
    from day27.constants import EVAL_QUERIES
    from rag.chunk_config import PRESET_CONFIGS
    from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment

    doc = parse_bytes(eval_sample_path.read_bytes(), eval_sample_path.name)
    queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]
    results = run_ab_experiment(doc, list(PRESET_CONFIGS), queries)
    best = pick_best_config(results)
    if best:
        store.set_chunk_config(best.config)
    return rebuild_store(store, include_sample_docs=include_sample_docs)
