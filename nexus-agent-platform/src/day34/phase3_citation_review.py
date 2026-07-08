"""Phase 3 Citation 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/citation_builder.py — Citation / CitationBundle",
    "rag/citation_config.py — enabled / max_citations",
    "RAGContextService.retrieve_citation_bundle",
    "GET/PUT /api/knowledge/citation-config",
    "POST /api/knowledge/citation-preview",
    "POST /api/chat — reply + citations[] + rewrite",
]


def main() -> int:
    print("=" * 58)
    print("  Day 34 Citation 回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
