"""
解析结果模型与格式注册

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".markdown", ".pdf"})

FORMAT_LABELS: dict[str, str] = {
    ".txt": "纯文本",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".pdf": "PDF",
}


@dataclass
class DocumentSection:
    """结构化章节（Markdown / PDF 页）"""

    title: str
    body: str
    level: int = 0
    index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body,
            "level": self.level,
            "index": self.index,
        }


@dataclass
class ParsedDocument:
    """统一解析输出 — 供 ingestion 与分块策略使用"""

    filename: str
    format: str
    plain_text: str
    title: str = ""
    sections: list[DocumentSection] = field(default_factory=list)
    page_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "format": self.format,
            "title": self.title,
            "plain_text_len": len(self.plain_text),
            "section_count": self.section_count,
            "page_count": self.page_count,
            "metadata": self.metadata,
        }
