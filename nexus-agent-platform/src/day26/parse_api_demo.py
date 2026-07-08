"""
Day 26 API 演示 — 上传 Markdown

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day26/parse_api_demo.py
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_SAMPLES = Path(__file__).resolve().parent / "sample_docs"
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

    print("=== Day 26 Parse API Demo ===\n")
    status = client.get("/api/knowledge/status").json()
    print(f"  formats: {status.get('supported_formats')}")

    md_bytes = (_SAMPLES / "product_notice.md").read_bytes()
    upload = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_notice.md", io.BytesIO(md_bytes), "text/markdown")},
    )
    print(f"\n  upload md: {upload.json()}")

    health = client.get("/api/health").json()
    print(f"\n  version: {health.get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
