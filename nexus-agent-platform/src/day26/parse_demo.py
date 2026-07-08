"""
文档解析演示 — Markdown / PDF

运行：
    cd nexus-agent-platform
    PYTHONPATH=src python3 src/day26/parse_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_SAMPLES = Path(__file__).resolve().parent / "sample_docs"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from tools.doc_parser import parse_bytes


def main() -> int:
    print("=" * 56)
    print("  Day 26 文档解析演示")
    print("=" * 56)

    md_path = _SAMPLES / "product_notice.md"
    md = parse_bytes(md_path.read_bytes(), md_path.name)
    print(f"\n  Markdown: {md.title}")
    print(f"    章节数: {md.section_count}")
    print(f"    首段: {md.sections[0].title if md.sections else '—'}")

    pdf_path = _SAMPLES / "product_notice.pdf"
    if pdf_path.is_file():
        pdf = parse_bytes(pdf_path.read_bytes(), pdf_path.name)
        print(f"\n  PDF: {pdf.title}")
        print(f"    页数: {pdf.page_count}")
        print(f"    文本预览: {pdf.plain_text[:80]}…")
    else:
        print("\n  PDF 样例缺失，跳过")

    print("\n  ✅ 解析演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
