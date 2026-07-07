"""
文档 ingestion 流水线 — 读取、解析、清洗、分块、入库

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import NexusError, StorageError
from rag.knowledge_store import KnowledgeDocument, KnowledgeStore, get_knowledge_store
from tools.doc_parser import detect_format, parse_bytes, supported_formats
from tools.doc_reader import read_documents


def ingest_directory(
    directory: Path,
    *,
    pattern: str = "*.txt",
    clean: bool = True,
    store: KnowledgeStore | None = None,
) -> list[KnowledgeDocument]:
    """批量将目录下文本文件写入知识库"""
    kb = store or get_knowledge_store()
    docs = read_documents(directory, pattern=pattern, clean=clean)
    results: list[KnowledgeDocument] = []
    for doc in docs:
        content = doc.cleaned if clean and doc.cleaned else doc.content
        meta = kb.ingest_text(content, filename=doc.name, clean=False)
        results.append(meta)
    kb.save()
    return results


def ingest_upload(
    data: bytes,
    filename: str,
    *,
    store: KnowledgeStore | None = None,
    uploads_dir: Path | None = None,
    chunk_strategy: str = "auto",
) -> KnowledgeDocument:
    """处理 API 上传：解析 → 落盘 → 入库"""
    from core.paths import get_path

    kb = store or get_knowledge_store()
    target_dir = uploads_dir or get_path("knowledge_uploads")
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    try:
        detect_format(safe_name)
    except NexusError as exc:
        raise ValueError(exc.message) from exc

    dest = target_dir / safe_name
    dest.write_bytes(data)
    meta = kb.ingest_bytes(
        data,
        filename=safe_name,
        chunk_strategy=chunk_strategy,
    )
    kb.save()
    return meta


__all__ = ["ingest_directory", "ingest_upload", "supported_formats"]
