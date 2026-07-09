"""
知识库全量重建演示

运行：PYTHONPATH=src python3 src/day28/rebuild_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag.chunk_config import ChunkConfig
from rag.knowledge_rebuild import collect_source_files, rebuild_store
from rag.knowledge_store import KnowledgeStore


def main() -> int:
    print("=" * 56)
    print("  Day 28 知识库全量重建演示")
    print("=" * 56)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_chunk_config(ChunkConfig(name="wide", chunk_size=400, overlap=60))
    print(f"\n  重建前: {store.document_count} 篇 / {store.chunk_count} 块")
    print(f"  配置: size={store.chunk_config.chunk_size} overlap={store.chunk_config.overlap}")

    sources = collect_source_files()
    print(f"  源文件: {[p.name for p in sources]}")

    report = rebuild_store(store)
    print(f"\n  重建后: {report.documents_after} 篇 / {report.chunks_after} 块")
    print(f"  处理源: {report.sources_processed} 个")
    print(f"  时间: {report.rebuilt_at}")
    print("\n  ✅ 重建演示完成")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
