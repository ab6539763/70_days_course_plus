"""
关键词检索演示

运行：python3 src/day19/retriever_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag import RAGContextService

QUERIES = [
    "年化收益率是多少",
    "投资有风险吗",
    "客服电话",
    "内部资料外传",
]


def main() -> int:
    service = RAGContextService.from_sample_docs()
    print("=== 关键词检索演示 ===\n")
    print(f"  索引块数: {service.index.chunk_count}\n")

    for q in QUERIES:
        print(service.retrieve_summary(q))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
