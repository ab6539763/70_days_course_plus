"""
关键词 vs 向量检索对比

运行：python3 src/day20/vector_search_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag import RAGContextService

QUERY = "投资回报率是多少"


def main() -> int:
    kw_service = RAGContextService.from_sample_docs(use_embedding=False)
    emb_service = RAGContextService.from_sample_docs(use_embedding=True)

    print("=== 关键词 vs 向量检索 ===\n")
    print(f"  查询: {QUERY}\n")

    kw_results = kw_service.index.search(QUERY, top_k=2)
    emb_results = emb_service.index.search(QUERY, top_k=2)

    print("  [KeywordRetriever]")
    if kw_results:
        for r in kw_results:
            print(f"    score={r.score:.0%} source={r.chunk.source} {r.preview(50)}")
    else:
        print("    （未命中）")

    print("\n  [EmbeddingRetriever]")
    for r in emb_results:
        print(f"    sim={r.score:.0%} source={r.chunk.source} {r.preview(50)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
