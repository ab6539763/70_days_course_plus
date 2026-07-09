"""
引用溯源演示 — 检索结果结构化 citations

运行：PYTHONPATH=src python3 src/day34/citation_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day34.constants import CITATION_QUERIES
from rag.knowledge_store import KnowledgeStore


def main() -> int:
    print("=" * 60)
    print("  Day 34 Citation 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_citation_config()
    print(f"\n  citation enabled={cfg.enabled} max={cfg.max_citations}")

    for item in CITATION_QUERIES:
        q = item["query"]
        data = store.fetch_citations(q)
        print(f"\n  Q: {q}")
        if data.get("rewrite") and data["rewrite"].get("changed"):
            print(f"    rewrite: {data['rewrite']['rewritten']!r}")
        for c in data.get("citations") or []:
            print(
                f"    [{c['rank']}] {c['source']} score={c['score']:.2f} "
                f"{c['preview'][:50]}…"
            )

    print("\n  ✅ Citation 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
