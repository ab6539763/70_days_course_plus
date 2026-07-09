"""
Query Rewrite API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day33/rewrite_api_demo.py
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

    print("=== Day 33 Rewrite API Demo ===\n")
    cfg = client.get("/api/knowledge/rewrite-config").json()
    print(f"  enabled={cfg.get('enabled')} mode={cfg.get('mode')}")

    preview = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "那个理财能赚多少"},
    )
    print(f"  preview: {preview.status_code} → {preview.json().get('rewritten')}")

    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    print(f"  PUT rewrite-config: {resp.status_code}")

    chat = client.post("/api/chat", json={"message": "那个理财能赚多少？"})
    print(f"  chat: {chat.status_code}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
