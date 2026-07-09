"""Phase 3 Query Rewrite 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/query_rewriter.py — RuleBasedQueryRewriter + DEFAULT_RULES",
    "rag/rewriting_retriever.py — 改写后委托 inner 检索",
    "rag/rewrite_config.py — enabled / mode / fallback",
    "GET/PUT /api/knowledge/rewrite-config",
    "POST /api/knowledge/rewrite-preview — 审计预览",
]


def main() -> int:
    print("=" * 58)
    print("  Day 33 Query Rewrite 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
