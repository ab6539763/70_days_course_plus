"""
增量索引演示

运行：PYTHONPATH=src python3 src/day30/incremental_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.knowledge_store import INDEX_MODE_INCREMENTAL, KnowledgeStore


def main() -> int:
    print("=" * 56)
    print("  Day 30 增量索引演示")
    print("=" * 56)

    tmp = Path("/tmp/day30_incremental_demo")
    tmp.mkdir(parents=True, exist_ok=True)
    store_path = tmp / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=store_path)
    store.chroma_path = tmp / "chroma"
    before_docs = store.document_count

    sample = _SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        print("  ⚠ 样例 md 缺失，跳过上传演示")
        return 0

    data = sample.read_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    after_first = store.document_count
    store.ingest_bytes(data, filename="notice.md", incremental=True)

    chroma = store._chroma_index()
    print(f"\n  初始文档数: {before_docs}")
    print(f"  首次上传后: {after_first} 篇 / {store.chunk_count} 块")
    print(f"  重复上传后文档数: {store.document_count}（应不增加）")
    print(f"  index_mode: {store.index_mode}")
    print(f"  chroma_count: {chroma.count()}")

    assert store.index_mode == INDEX_MODE_INCREMENTAL
    assert chroma.count() == store.chunk_count
    assert store.document_count == after_first

    print("\n  ✅ 增量索引演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
