"""Phase 3 Chroma 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/chroma_store.py — ChromaVectorIndex 持久化",
    "rag/chroma_retriever.py — ChromaEmbeddingRetriever",
    "store.json 保留 TF-IDF 词表，向量落盘 Chroma",
    "POST /api/knowledge/rebuild 流程不变，索引引擎换 Chroma",
    "status 暴露 vector_backend / chroma_count",
]


def main() -> int:
    print("=" * 58)
    print("  Day 29 Chroma 向量库回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
