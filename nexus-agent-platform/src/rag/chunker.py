"""
文档分块 — RAG 检索前置步骤

将长文档切分为带重叠的文本块，供关键词检索器索引。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from tools.doc_reader import DocumentRecord

# 段落分隔：空行或连续换行
_PARA_SPLIT = re.compile(r"\n\s*\n+")


@dataclass(frozen=True)
class TextChunk:
    """单个文本块"""

    chunk_id: str
    text: str
    source: str
    index: int
    start_char: int
    end_char: int

    @property
    def char_count(self) -> int:
        return len(self.text)


def chunk_text(
    text: str,
    *,
    chunk_size: int = 200,
    overlap: int = 40,
    source: str = "",
) -> list[TextChunk]:
    """
    将文本切分为重叠块。

    策略：先按段落合并，再按字符窗口滑动切分，保留 overlap 避免语义断裂。

    Args:
        text: 原始文本
        chunk_size: 单块最大字符数
        overlap: 相邻块重叠字符数
        source: 来源标识（文件名等）

    Returns:
        TextChunk 列表
    """
    text = (text or "").strip()
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正整数")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须满足 0 <= overlap < chunk_size")

    paragraphs = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    merged = _merge_paragraphs(paragraphs, chunk_size)
    chunks: list[TextChunk] = []
    offset = 0

    for block_idx, block in enumerate(merged):
        if len(block) <= chunk_size:
            chunk = TextChunk(
                chunk_id=f"{source or 'doc'}:{block_idx}:0",
                text=block,
                source=source,
                index=len(chunks),
                start_char=offset,
                end_char=offset + len(block),
            )
            chunks.append(chunk)
            offset += len(block) + 1
            continue

        step = chunk_size - overlap
        start = 0
        sub_idx = 0
        while start < len(block):
            piece = block[start : start + chunk_size]
            chunk = TextChunk(
                chunk_id=f"{source or 'doc'}:{block_idx}:{sub_idx}",
                text=piece,
                source=source,
                index=len(chunks),
                start_char=offset + start,
                end_char=offset + start + len(piece),
            )
            chunks.append(chunk)
            sub_idx += 1
            if start + chunk_size >= len(block):
                break
            start += step

        offset += len(block) + 1

    return chunks


def chunk_documents(
    docs: list[DocumentRecord],
    *,
    chunk_size: int = 200,
    overlap: int = 40,
    use_cleaned: bool = True,
) -> list[TextChunk]:
    """批量分块多份文档"""
    all_chunks: list[TextChunk] = []
    for doc in docs:
        content = doc.cleaned if use_cleaned and doc.cleaned else doc.content
        chunks = chunk_text(
            content,
            chunk_size=chunk_size,
            overlap=overlap,
            source=doc.name,
        )
        all_chunks.extend(chunks)
    return all_chunks


def _merge_paragraphs(paragraphs: list[str], chunk_size: int) -> list[str]:
    """将短段落合并，减少碎片块"""
    merged: list[str] = []
    buffer = ""

    for para in paragraphs:
        if not buffer:
            buffer = para
        elif len(buffer) + 1 + len(para) <= chunk_size:
            buffer = f"{buffer}\n{para}"
        else:
            merged.append(buffer)
            buffer = para

    if buffer:
        merged.append(buffer)

    return merged
