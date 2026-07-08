"""
分块策略对比演示

运行：PYTHONPATH=src python3 src/day26/chunk_compare_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_SAMPLES = Path(__file__).resolve().parent / "sample_docs"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.chunk_strategies import compare_strategies
from tools.doc_parser import parse_bytes


def main() -> int:
    print("=" * 56)
    print("  Day 26 分块策略对比")
    print("=" * 56)

    md = parse_bytes(
        (_SAMPLES / "product_notice.md").read_bytes(),
        "product_notice.md",
    )
    results = compare_strategies(md)
    for r in results:
        print(f"\n  策略 {r.strategy}: {r.chunk_count} 块")
        print(f"    预览: {r.preview[:60]}…")

    print("\n  ✅ 对比完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
