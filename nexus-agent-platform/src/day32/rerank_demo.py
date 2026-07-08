"""
Rerank 演示 — 对比关闭 / 开启精排

运行：PYTHONPATH=src python3 src/day32/rerank_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day32.constants import RERANK_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rerank_config import RerankConfig
from rag.reranking_retriever import RerankingRetriever
from rag.rewriting_retriever import RewritingRetriever


def _top_hit(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rerank_config(RerankConfig(enabled=enabled, candidate_pool=20))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if not isinstance(retriever, RewritingRetriever):
        raise RuntimeError("expected RewritingRetriever")
    if not isinstance(retriever.inner, RerankingRetriever):
        raise RuntimeError("expected RerankingRetriever inner")
    hits = retriever.search(query, top_k=1)
    if not hits:
        return "—"
    preview = hits[0].chunk.text[:40].replace("\n", " ")
    label = "rerank" if enabled else "recall"
    return f"[{label}] {hits[0].chunk.source} ({hits[0].score:.2f}) {preview}…"


def main() -> int:
    print("=" * 60)
    print("  Day 32 Rerank 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rerank_config()
    print(f"\n  默认 rerank: enabled={cfg.enabled} pool={cfg.candidate_pool}")

    for item in RERANK_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭精排 → {_top_hit(store, q, enabled=False)}")
        print(f"    开启精排 → {_top_hit(store, q, enabled=True)}")

    print("\n  ✅ Rerank 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
