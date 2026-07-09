"""Day 26 文档解析器测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
SAMPLES = SRC / "day26" / "sample_docs"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.exceptions import NexusError
from rag.chunk_strategies import chunk_from_parsed, compare_strategies
from tools.doc_parser import parse_bytes, supported_formats
from tools.parsers.markdown_parser import parse_markdown


def test_supported_formats_includes_md_pdf():
    exts = {f["extension"] for f in supported_formats()}
    assert ".md" in exts
    assert ".pdf" in exts


def test_parse_markdown_sections():
    data = (SAMPLES / "product_notice.md").read_bytes()
    doc = parse_markdown(data, "product_notice.md")
    assert doc.format == "markdown"
    assert doc.section_count >= 4
    assert "收益率" in doc.plain_text or "8%" in doc.plain_text
    titles = [s.title for s in doc.sections]
    assert any("风险" in t for t in titles)


def test_markdown_strips_code_fence():
    raw = b"# T\n\n```py\nsecret()\n```\n\n## Body\nvisible text"
    doc = parse_markdown(raw, "t.md")
    assert "secret()" not in doc.plain_text
    assert "visible text" in doc.plain_text


def test_parse_pdf_sample():
    pdf_path = SAMPLES / "product_notice.pdf"
    if not pdf_path.is_file():
        pytest.skip("sample pdf missing")
    doc = parse_bytes(pdf_path.read_bytes(), "product_notice.pdf")
    assert doc.format == "pdf"
    assert doc.page_count >= 1
    assert "1000" in doc.plain_text


def test_parse_bytes_rejects_unknown_ext():
    with pytest.raises(NexusError):
        parse_bytes(b"data", "file.docx")


def test_chunk_markdown_auto_strategy():
    doc = parse_bytes((SAMPLES / "product_notice.md").read_bytes(), "product_notice.md")
    chunks = chunk_from_parsed(doc, strategy="markdown")
    assert len(chunks) >= 3
    assert any("起购" in c.text or "1000" in c.text for c in chunks)


def test_compare_strategies_differs():
    doc = parse_bytes((SAMPLES / "product_notice.md").read_bytes(), "product_notice.md")
    results = compare_strategies(doc)
    assert len(results) == 2
    assert results[0].strategy == "fixed"
    assert results[1].strategy == "markdown"


def test_parse_empty_raises():
    with pytest.raises(NexusError):
        parse_bytes(b"", "empty.txt")


def test_invalid_pdf_raises():
    with pytest.raises(NexusError):
        parse_bytes(b"%PDF-1.4\nbroken", "bad.pdf")


def test_plain_text_utf8():
    doc = parse_bytes("你好世界".encode("utf-8"), "hello.txt")
    assert doc.plain_text == "你好世界"
    assert doc.format == "txt"
