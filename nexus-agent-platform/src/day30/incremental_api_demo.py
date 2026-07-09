"""
增量索引 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


def main() -> int:
    store = KnowledgeStore.bootstrap_from_sample_docs()
    set_knowledge_store(store)
    client = TestClient(create_app())

    print("=== Day 30 Incremental API Demo ===\n")
    sample = _SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        print("  sample md missing")
        return 1

    before = client.get("/api/knowledge/status").json()
    print(f"  before: {before['chunk_count']} chunks, mode={before.get('index_mode')}")

    with sample.open("rb") as fh:
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    print(f"  upload: {resp.status_code} index_mode={resp.json().get('index_mode')}")

    with sample.open("rb") as fh:
        resp2 = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    after = client.get("/api/knowledge/status").json()
    print(f"  re-upload docs={after['document_count']} chroma={after['chroma_count']}")
    print(f"  last_incremental_at: {after.get('last_incremental_at')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
