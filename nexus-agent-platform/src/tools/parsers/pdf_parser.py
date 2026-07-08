"""
PDF 文本抽取 — 基于 pypdf

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import io

from core.exceptions import NexusError, StorageError
from tools.parsers.base import DocumentSection, ParsedDocument


def parse_pdf(data: bytes, filename: str) -> ParsedDocument:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise NexusError(
            "PDF 解析需要安装 pypdf：pip install pypdf",
            code="PDF_DEPS_MISSING",
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise NexusError(f"无法解析 PDF: {filename}", code="PDF_PARSE_ERROR") from exc

    pages: list[str] = []
    sections: list[DocumentSection] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        pages.append(text)
        if text:
            sections.append(
                DocumentSection(
                    title=f"第{i + 1}页",
                    body=text,
                    level=0,
                    index=i,
                )
            )

    plain_text = "\n\n".join(p for p in pages if p).strip()
    if not plain_text:
        raise NexusError(f"PDF 未提取到文本: {filename}", code="PDF_EMPTY")

    title = filename.rsplit(".", 1)[0]
    return ParsedDocument(
        filename=filename,
        format="pdf",
        plain_text=plain_text,
        title=title,
        sections=sections,
        page_count=len(reader.pages),
        metadata={"extractor": "pypdf"},
    )
