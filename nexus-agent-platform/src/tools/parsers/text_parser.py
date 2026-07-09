"""
纯文本解析

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from tools.parsers.base import ParsedDocument


def parse_plain_text(data: bytes, filename: str) -> ParsedDocument:
    text = data.decode("utf-8").strip()
    title = filename.rsplit(".", 1)[0]
    return ParsedDocument(
        filename=filename,
        format="txt",
        plain_text=text,
        title=title,
        metadata={"encoding": "utf-8"},
    )
