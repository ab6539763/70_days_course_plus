"""Phase 3 增量索引日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/knowledge_incremental.py — IncrementalReport",
    "_incremental_index — upload 不 reset Chroma",
    "_remove_document_by_source — 同名上传替换",
    "chroma_store.delete_by_ids / delete_by_source",
    "rebuild 仍走全量 _rebuild_index",
]


def main() -> int:
    print("=" * 58)
    print("  Day 30 增量索引回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
