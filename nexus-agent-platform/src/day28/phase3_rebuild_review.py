"""Phase 3 重建日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/knowledge_rebuild.py — collect_source_files / rebuild_store",
    "POST /api/knowledge/rebuild — 全量重建 API",
    "sample_docs + uploads 双源扫描",
    "apply_best_config — 评估后自动重建",
    "last_rebuilt_at 持久化",
]


def main() -> int:
    print("=" * 58)
    print("  Day 28 知识库重建回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
