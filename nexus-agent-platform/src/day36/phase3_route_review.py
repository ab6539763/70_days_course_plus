"""Phase 3 Routing 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/query_router.py — RuleBasedQueryRouter / RouteResult",
    "rag/routing_retriever.py — 动态 expand/rewrite 开关",
    "rag/route_config.py — faq_fast / rag_standard / rag_wide",
    "GET/PUT /api/knowledge/route-config",
    "POST /api/knowledge/route-preview",
    "POST /api/chat — route 审计元数据",
]


def main() -> int:
    print("=" * 58)
    print("  Day 36 Query Router 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
