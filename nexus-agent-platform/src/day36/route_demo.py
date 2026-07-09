"""
检索管线路由演示 — 意图 → expand/rewrite 开关

运行：PYTHONPATH=src python3 src/day36/route_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day36.constants import ROUTE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.query_router import RuleBasedQueryRouter


def main() -> int:
    print("=" * 60)
    print("  Day 36 Query Router 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_route_config()
    router = RuleBasedQueryRouter(config=cfg)
    print(f"\n  route enabled={cfg.enabled} fallback={cfg.fallback_intent}")

    for item in ROUTE_QUERIES:
        q = item["query"]
        route = router.route(q)
        print(f"\n  Q: {q}")
        print(f"    intent={route.intent} expand={route.expand} rewrite={route.rewrite}")
        print(f"    label: {route.label}")
        data = store.fetch_citations(q)
        if data.get("route"):
            print(f"    routed expand={data['route']['expand']}")

    print("\n  ✅ Route 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
