"""Phase 3 Validation Retry 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/validation_retry.py — apply_validation_retry / rag_wide 重检索",
    "KnowledgeStore.fetch_citations_retry — 放大 pool + intent_override",
    "POST /api/knowledge/validation-retry-preview",
    "POST /api/chat — retry_on_fail 循环后再拒答",
    "validation.retries + retry_route 审计字段",
]


def main() -> int:
    print("=" * 58)
    print("  Day 38 多轮 Self-RAG 重试回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
