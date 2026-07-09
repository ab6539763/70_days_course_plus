"""
Markdown 结构解析 — 标题分段、去代码块

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import re

from tools.parsers.base import DocumentSection, ParsedDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def parse_markdown(data: bytes, filename: str) -> ParsedDocument:
    raw = data.decode("utf-8")
    stripped = _FENCE.sub("", raw)
    stripped = _INLINE_CODE.sub(r"\1", stripped)
    stripped = _LINK.sub(r"\1", stripped)
    stripped = _BOLD.sub(r"\1", stripped)

    sections: list[DocumentSection] = []
    title = filename.rsplit(".", 1)[0]
    current_title = title
    current_level = 0
    current_lines: list[str] = []
    idx = 0

    for line in stripped.splitlines():
        match = _HEADING.match(line)
        if match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(
                        DocumentSection(
                            title=current_title,
                            body=body,
                            level=current_level,
                            index=idx,
                        )
                    )
                    idx += 1
            level = len(match.group(1))
            current_title = match.group(2).strip()
            current_level = level
            if level == 1 and not sections:
                title = current_title
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(
                DocumentSection(
                    title=current_title,
                    body=body,
                    level=current_level,
                    index=idx,
                )
            )

    plain_parts = [f"## {s.title}\n{s.body}" for s in sections if s.body]
    plain_text = "\n\n".join(plain_parts) if plain_parts else stripped.strip()

    return ParsedDocument(
        filename=filename,
        format="markdown",
        plain_text=plain_text,
        title=title,
        sections=sections,
        metadata={"heading_count": len(sections)},
    )
