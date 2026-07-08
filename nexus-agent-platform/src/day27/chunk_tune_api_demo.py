"""
分块调参 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day27/chunk_tune_api_demo.py
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

    print("=== Day 27 Chunk Tune API Demo ===\n")
    cfg = client.get("/api/knowledge/chunk-config").json()
    print(f"  GET chunk-config: {cfg}")

    updated = client.put(
        "/api/knowledge/chunk-config",
        json={"chunk_size": 300, "overlap": 50, "strategy": "auto", "name": "tuned"},
    )
    print(f"\n  PUT chunk-config: {updated.json()}")

    ev = client.post("/api/knowledge/evaluate", json={"use_presets": True})
    print(f"\n  POST evaluate best: {ev.json().get('best_config')}")
    print(f"  eval queries: {ev.json().get('eval_query_count')}")

    health = client.get("/api/health").json()
    print(f"\n  version: {health.get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
