"""
Self-RAG 答案校验演示 — reply vs citations 一致性

运行：PYTHONPATH=src python3 src/day37/validation_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day37.constants import VALIDATION_CASES
from rag.answer_validator import RuleBasedAnswerValidator
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import ValidationConfig


def main() -> int:
    print("=" * 60)
    print("  Day 37 Self-RAG 答案校验演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_validation_config()
    validator = RuleBasedAnswerValidator(config=cfg)
    print(f"\n  validation enabled={cfg.enabled} min_score={cfg.min_score}")

    for item in VALIDATION_CASES:
        q = item["query"]
        reply = item["reply"]
        cite_data = store.fetch_citations(q)
        citations = cite_data.get("citations") or []
        result = validator.validate(q, reply, citations)
        flag = "✅" if result.passed == item["expect_passed"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    passed={result.passed} score={result.score:.2f} {flag}")
        print(f"    reason: {result.reason}")
        if citations:
            print(f"    citations: {len(citations)} matched={list(result.matched_citation_ranks)}")

    print("\n  ✅ Validation 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
