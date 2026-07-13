"""
文档分块演示

运行：python3 src/day19/chunk_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.paths import get_path
from rag import chunk_text
from tools.doc_reader import read_document


def main() -> int:
    doc = read_document(get_path("sample_docs") / "raw_notice.txt", clean=True)
    text = doc.cleaned or doc.content
    chunks = chunk_text(text, chunk_size=120, overlap=20, source=doc.name)

    print("=== 文档分块演示 ===\n")
    print(f"  原文长度: {len(text)} 字符")
    print(f"  分块数量: {len(chunks)}\n")

    for c in chunks:
        preview = c.text.replace("\n", " ")[:70]
        print(f"  [{c.chunk_id}] {preview}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
