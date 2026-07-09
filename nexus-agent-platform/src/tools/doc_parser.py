"""
统一文档解析入口 — 按扩展名分发

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import NexusError, StorageError
from tools.parsers.base import FORMAT_LABELS, SUPPORTED_EXTENSIONS, ParsedDocument
from tools.parsers.markdown_parser import parse_markdown
from tools.parsers.pdf_parser import parse_pdf
from tools.parsers.text_parser import parse_plain_text


def detect_format(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise NexusError(
            f"不支持的文件格式: {ext}，支持: {sorted(SUPPORTED_EXTENSIONS)}",
            code="UNSUPPORTED_FORMAT",
        )
    return ext


def parse_bytes(data: bytes, filename: str) -> ParsedDocument:
    """
    将上传字节解析为统一 ParsedDocument。

    Raises:
        StorageError: 格式不支持或解析失败
        UnicodeDecodeError: 文本文件非 UTF-8
    """
    if not data:
        raise NexusError("文件内容为空", code="EMPTY_FILE")

    ext = detect_format(filename)
    safe_name = Path(filename).name

    if ext == ".txt":
        doc = parse_plain_text(data, safe_name)
    elif ext in (".md", ".markdown"):
        doc = parse_markdown(data, safe_name)
    elif ext == ".pdf":
        doc = parse_pdf(data, safe_name)
    else:
        raise NexusError(f"未实现的格式: {ext}", code="UNSUPPORTED_FORMAT")

    doc.metadata.setdefault("format_label", FORMAT_LABELS.get(ext, ext))
    return doc


def supported_formats() -> list[dict[str, str]]:
    """API 返回的支持格式列表"""
    seen: set[str] = set()
    items: list[dict[str, str]] = []
    for ext in sorted(SUPPORTED_EXTENSIONS):
        if ext in seen:
            continue
        items.append({"extension": ext, "label": FORMAT_LABELS.get(ext, ext)})
        seen.add(ext)
    return items
