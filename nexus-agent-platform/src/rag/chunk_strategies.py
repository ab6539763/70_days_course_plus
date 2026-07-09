"""
分块策略 — 固定窗口 vs Markdown 章节

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.chunker import TextChunk, chunk_text
from tools.parsers.base import DocumentSection, ParsedDocument


@dataclass
class ChunkStrategyResult:
    """策略对比结果"""

    strategy: str
    chunk_count: int
    chunks: list[TextChunk]
    preview: str


def chunk_fixed_window(
    text: str,
    *,
    source: str,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """Day 19 默认滑动窗口策略"""
    return chunk_text(text, chunk_size=chunk_size, overlap=overlap, source=source)


def chunk_markdown_sections(
    doc: ParsedDocument,
    *,
    max_chars: int = 400,
    overlap: int = 40,
) -> list[TextChunk]:
    """
    按 Markdown 章节分块：每节独立成块，过长再滑动切分。
    """
    if not doc.sections:
        return chunk_fixed_window(doc.plain_text, source=doc.filename)

    chunks: list[TextChunk] = []
    global_index = 0

    for section in doc.sections:
        header = f"[{section.title}] "
        body = section.body.strip()
        piece = f"{header}{body}" if body else section.title

        if len(piece) <= max_chars:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}",
                    text=piece,
                    source=doc.filename,
                    index=global_index,
                    start_char=0,
                    end_char=len(piece),
                )
            )
            global_index += 1
            continue

        sub_chunks = chunk_text(
            piece,
            chunk_size=max_chars,
            overlap=overlap,
            source=doc.filename,
        )
        for sub in sub_chunks:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}:{sub.index}",
                    text=sub.text,
                    source=doc.filename,
                    index=global_index,
                    start_char=sub.start_char,
                    end_char=sub.end_char,
                )
            )
            global_index += 1

    return chunks


def chunk_from_parsed(
    doc: ParsedDocument,
    *,
    strategy: str = "auto",
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """根据文档类型与策略选择分块方式"""
    chosen = strategy
    if strategy == "auto":
        chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"

    if chosen == "markdown":
        return chunk_markdown_sections(doc, max_chars=chunk_size, overlap=overlap)
    return chunk_fixed_window(
        doc.plain_text,
        source=doc.filename,
        chunk_size=chunk_size,
        overlap=overlap,
    )


def compare_strategies(doc: ParsedDocument) -> list[ChunkStrategyResult]:
    """对比固定窗口与章节策略（教学演示用）"""
    fixed = chunk_fixed_window(doc.plain_text, source=doc.filename)
    section = chunk_markdown_sections(doc) if doc.sections else fixed

    return [
        ChunkStrategyResult(
            strategy="fixed",
            chunk_count=len(fixed),
            chunks=fixed,
            preview=fixed[0].text[:80] if fixed else "",
        ),
        ChunkStrategyResult(
            strategy="markdown",
            chunk_count=len(section),
            chunks=section,
            preview=section[0].text[:80] if section else "",
        ),
    ]
