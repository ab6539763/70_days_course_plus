"""
文档 ingestion 流水线 — 读取、清洗、分块、入库

需求：ZL-NA-REQ-025
"""

from __future__ import annotations

from pathlib import Path

from rag.knowledge_store import KnowledgeDocument, KnowledgeStore, get_knowledge_store
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
) -> KnowledgeDocument:
    """处理 API 上传：落盘 + 入库"""
    from core.paths import get_path

    kb = store or get_knowledge_store()
    target_dir = uploads_dir or get_path("knowledge_uploads")
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".txt"):
        raise ValueError("仅支持 .txt 文本文件")

    dest = target_dir / safe_name
    dest.write_bytes(data)
    meta = kb.ingest_bytes(data, filename=safe_name)
    kb.save()
    return meta
