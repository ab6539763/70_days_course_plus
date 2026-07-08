"""
重建 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day28/rebuild_api_demo.py
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
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())
    client = TestClient(create_app())

    print("=== Day 28 Rebuild API Demo ===\n")
    resp = client.post(
        "/api/knowledge/rebuild",
        json={"include_sample_docs": True, "apply_best_config": False},
    )
    print(f"  POST rebuild: {resp.status_code}")
    data = resp.json()
    print(f"    chunks {data.get('chunks_before')} → {data.get('chunks_after')}")
    print(f"    sources: {data.get('source_files')}")

    status = client.get("/api/knowledge/status").json()
    print(f"\n  last_rebuilt_at: {status.get('last_rebuilt_at')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
