"""Phase 3 Rerank 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/reranker.py — MockCrossEncoder 逐对打分",
    "rag/reranking_retriever.py — hybrid 召回 + rerank 精排",
    "rag/rerank_config.py — enabled / candidate_pool",
    "GET/PUT /api/knowledge/rerank-config",
    "KnowledgeStore 默认开启 rerank",
]


def main() -> int:
    print("=" * 58)
    print("  Day 32 Rerank 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
