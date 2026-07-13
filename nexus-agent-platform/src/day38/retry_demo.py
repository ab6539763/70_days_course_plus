"""
多轮 Self-RAG 重试演示 — 校验失败后 rag_wide 重检索

运行：PYTHONPATH=src python3 src/day38/retry_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day38.constants import RETRY_CASES
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def main() -> int:
    print("=" * 60)
    print("  Day 38 多轮 Self-RAG 重试演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            refuse_on_fail=False,
            retry_on_fail=True,
            max_retries=1,
        )
    )

    for item in RETRY_CASES:
        q = item["query"]
        reply = item["reply"]
        cite_data = store.fetch_citations(q)
        citations = cite_data.get("citations") or []
        outcome = apply_validation_retry(store, q, reply, citations, cite_data)
        assert outcome is not None
        flag = "✅" if outcome.validation.passed == item["expect_passed_after_retry"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    retries={outcome.validation.retries} passed={outcome.validation.passed} {flag}")
        print(f"    reason: {outcome.validation.reason}")
        route = outcome.cite_data.get("route")
        if route:
            print(f"    route: {route.get('intent')} expand={route.get('expand')}")

    print("\n  ✅ Retry 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
