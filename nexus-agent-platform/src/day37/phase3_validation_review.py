"""Phase 3 Validation 日回顾"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ITEMS = [
    "rag/answer_validator.py — RuleBasedAnswerValidator / ValidationResult",
    "rag/validation_config.py — min_score / refuse_on_fail",
    "GET/PUT /api/knowledge/validation-config",
    "POST /api/knowledge/validation-preview",
    "POST /api/chat — validation 审计元数据",
]


def main() -> int:
    print("=" * 58)
    print("  Day 37 Self-RAG 答案校验回顾")
    print("=" * 58)
    for item in ITEMS:
        print(f"    • {item}")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
