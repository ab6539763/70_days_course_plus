"""
Day 27 Phase 3 回顾 — 分块调参

运行：python3 src/day27/phase3_tune_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/chunk_config.py — ChunkConfig 与预设",
    "rag/retrieval_eval.py — hit@1 评估与 A/B",
    "GET/PUT /api/knowledge/chunk-config",
    "POST /api/knowledge/evaluate",
    "KnowledgeStore 持久化 chunk_config",
]


def main() -> int:
    print("=" * 58)
    print("  Day 27 分块调参回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
