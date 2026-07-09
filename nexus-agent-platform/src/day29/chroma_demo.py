"""
Chroma 向量库演示

运行：PYTHONPATH=src python3 src/day29/chroma_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.chroma_store import VECTOR_BACKEND
from rag.knowledge_store import KnowledgeStore


def main() -> int:
    print("=" * 56)
    print("  Day 29 Chroma 向量库演示")
    print("=" * 56)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    status = store.status_dict()
    print(f"\n  向量后端: {status['vector_backend']}")
    print(f"  Chroma 路径: {status['chroma_path']}")
    print(f"  块数: {store.chunk_count} / Chroma: {status['chroma_count']}")

    rag = store.as_rag_service()
    ctx = rag.retrieve_context("年化收益率是多少？")
    print(f"\n  检索上下文预览:\n  {ctx[:200]}...")

    assert status["vector_backend"] == VECTOR_BACKEND
    assert status["chroma_count"] == store.chunk_count

    print("\n  ✅ Chroma 演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
