"""
RAG 上下文构建演示

运行：python3 src/day19/rag_context_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag import RAGContextService

QUERY = "这份理财产品的年化收益率和风险提示是什么？"


def main() -> int:
    service = RAGContextService.from_sample_docs()
    context = service.retrieve_context(QUERY, top_k=2, max_chars=500)

    print("=== RAG 上下文构建 ===\n")
    print(f"  查询: {QUERY}\n")
    print("  【拼接后的 context】")
    print("-" * 50)
    print(context)
    print("-" * 50)
    print(f"\n  context 长度: {len(context)} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
