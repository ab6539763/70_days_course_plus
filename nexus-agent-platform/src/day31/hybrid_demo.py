"""
混合检索演示 — 对比 vector / keyword / hybrid

运行：PYTHONPATH=src python3 src/day31/hybrid_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day31.constants import HYBRID_QUERIES
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import (
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)


def _top_source(store: KnowledgeStore, query: str, mode: str) -> str:
    cfg = RetrievalConfig(mode=mode)
    store.set_retrieval_config(cfg)
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if isinstance(retriever, RerankingRetriever):
        retriever = retriever.inner
    if not isinstance(retriever, HybridRetriever):
        raise RuntimeError("expected HybridRetriever")
    hits = retriever.search(query, top_k=1)
    if not hits:
        return "—"
    preview = hits[0].chunk.text[:40].replace("\n", " ")
    return f"{hits[0].chunk.source} ({hits[0].score:.2f}) {preview}…"


def main() -> int:
    print("=" * 60)
    print("  Day 31 混合检索演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID))
    print(f"\n  默认模式: {store.get_retrieval_config().mode}")
    print(f"  融合: {store.get_retrieval_config().fusion}")

    for item in HYBRID_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        for mode in (MODE_VECTOR, MODE_KEYWORD, MODE_HYBRID):
            print(f"    {mode:8s} → {_top_source(store, q, mode)}")

    print("\n  ✅ 混合检索演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
