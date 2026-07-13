"""
Rerank API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
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

    print("=== Day 32 Rerank API Demo ===\n")
    cfg = client.get("/api/knowledge/rerank-config").json()
    print(f"  enabled={cfg.get('enabled')} pool={cfg.get('candidate_pool')}")

    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 20, "model": "mock"},
    )
    print(f"  PUT rerank-config: {resp.status_code}")

    status = client.get("/api/knowledge/status").json()
    print(f"  rerank enabled: {status.get('rerank_config', {}).get('enabled')}")

    chat = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    print(f"  chat: {chat.status_code}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
