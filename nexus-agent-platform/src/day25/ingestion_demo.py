"""
知识库 ingestion 演示

运行：
    cd nexus-agent-platform
    PYTHONPATH=src python3 src/day25/ingestion_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day25.constants import SAMPLE_UPLOAD_TEXT
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


def main() -> int:
    print("=" * 56)
    print("  Day 25 知识库 Ingestion 演示")
    print("=" * 56)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    print(f"\n  引导 sample_docs: {store.document_count} 篇, {store.chunk_count} 块")

    meta = store.ingest_text(
        SAMPLE_UPLOAD_TEXT,
        filename="custom_faq.txt",
    )
    print(f"  入库 custom_faq.txt: +{meta.chunk_count} 块")

    rag = store.as_rag_service()
    ctx = rag.retrieve_context("最低起购金额")
    print(f"\n  检索「最低起购金额」上下文片段:\n  {ctx[:200]}…")

    set_knowledge_store(store)
    print("\n  ✅ ingestion 演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
