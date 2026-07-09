"""
多查询扩展演示 — 单问句 → 多路 query → 合并 citations

运行：PYTHONPATH=src python3 src/day35/expansion_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day35.constants import EXPANSION_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.query_expander import build_expander


def main() -> int:
    print("=" * 60)
    print("  Day 35 Query Expansion 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_expansion_config()
    expander = build_expander(cfg)
    print(f"\n  expansion enabled={cfg.enabled} mode={cfg.mode} max={cfg.max_queries}")

    for item in EXPANSION_QUERIES:
        q = item["query"]
        exp = expander.expand(q)
        print(f"\n  Q: {q}")
        print(f"    queries ({len(exp.queries)}): {list(exp.queries)}")
        data = store.fetch_citations(q)
        cites = data.get("citations") or []
        print(f"    merged citations: {len(cites)}")
        if cites:
            print(f"    top1: {cites[0]['source']} score={cites[0]['score']:.2f}")

    print("\n  ✅ Expansion 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
