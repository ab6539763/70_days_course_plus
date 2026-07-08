"""
混合检索 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
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

    print("=== Day 31 Hybrid API Demo ===\n")
    cfg = client.get("/api/knowledge/retrieval-config").json()
    print(f"  mode={cfg.get('mode')} fusion={cfg.get('fusion')}")

    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "hybrid", "fusion": "rrf", "keyword_weight": 0.4, "vector_weight": 0.6},
    )
    print(f"  PUT retrieval-config: {resp.status_code}")

    status = client.get("/api/knowledge/status").json()
    print(f"  retrieval mode: {status.get('retrieval_config', {}).get('mode')}")

    chat = client.post("/api/chat", json={"message": "最低起购金额？"})
    print(f"  chat: {chat.status_code}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
