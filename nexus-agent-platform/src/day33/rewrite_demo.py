"""
查询改写演示 — 对比关闭 / 开启规则改写

运行：PYTHONPATH=src python3 src/day33/rewrite_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day33.constants import REWRITE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rewrite_config import RewriteConfig
from rag.retriever_stack import find_rewriting


def _preview(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rewrite_config(RewriteConfig(enabled=enabled))
    rag = store.as_rag_service()
    retriever = find_rewriting(rag.index.retriever)
    retriever.search(query, top_k=1)
    rw = retriever.last_rewrite
    if not rw:
        return "—"
    label = "rewrite" if enabled else "passthrough"
    return f"[{label}] {rw.rewritten!r} (rule={rw.rule_id or '—'})"


def main() -> int:
    print("=" * 60)
    print("  Day 33 Query Rewrite 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rewrite_config()
    print(f"\n  默认 rewrite: enabled={cfg.enabled} mode={cfg.mode}")

    for item in REWRITE_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭改写 → {_preview(store, q, enabled=False)}")
        print(f"    开启改写 → {_preview(store, q, enabled=True)}")

    print("\n  ✅ Query Rewrite 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
