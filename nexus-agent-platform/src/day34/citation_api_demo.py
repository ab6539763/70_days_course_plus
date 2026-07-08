"""
Citation API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day34/citation_api_demo.py
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

    print("=== Day 34 Citation API Demo ===\n")
    cfg = client.get("/api/knowledge/citation-config").json()
    print(f"  enabled={cfg.get('enabled')} max={cfg.get('max_citations')}")

    preview = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "那个理财能赚多少"},
    )
    print(f"  citation-preview: {preview.status_code}")
    cites = preview.json().get("citations") or []
    print(f"  citations count: {len(cites)}")
    if cites:
        print(f"  top1 source: {cites[0].get('source')}")

    chat = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    print(f"  chat: {chat.status_code}")
    body = chat.json()
    print(f"  chat citations: {len(body.get('citations') or [])}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
