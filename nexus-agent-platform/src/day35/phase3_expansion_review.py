"""Phase 3 Expansion 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/query_expander.py — Template / HyDE mock 扩展",
    "rag/expanding_retriever.py — 多路检索 + merge",
    "rag/result_merger.py — chunk_id 去重",
    "GET/PUT /api/knowledge/expansion-config",
    "POST /api/knowledge/expansion-preview",
    "POST /api/chat — expansion 审计元数据",
]


def main() -> int:
    print("=" * 58)
    print("  Day 35 Query Expansion 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
