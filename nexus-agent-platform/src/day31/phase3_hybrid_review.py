"""Phase 3 混合检索日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/hybrid_retriever.py — 关键词 + 向量融合",
    "rag/retrieval_config.py — mode / fusion / 权重",
    "GET/PUT /api/knowledge/retrieval-config",
    "KnowledgeStore 默认 hybrid 检索",
    "weighted 与 RRF 两种融合策略",
]


def main() -> int:
    print("=" * 58)
    print("  Day 31 混合检索回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
