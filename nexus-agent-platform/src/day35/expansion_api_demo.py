"""
Expansion API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day35/expansion_api_demo.py
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

    print("=== Day 35 Expansion API Demo ===\n")
    cfg = client.get("/api/knowledge/expansion-config").json()
    print(f"  enabled={cfg.get('enabled')} mode={cfg.get('mode')} max={cfg.get('max_queries')}")

    preview = client.post(
        "/api/knowledge/expansion-preview",
        json={"query": "理财安全吗"},
    )
    print(f"  expansion-preview: {preview.status_code}")
    body = preview.json()
    print(f"  queries: {body.get('queries')}")

    cite = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    print(f"  citation-preview: {cite.status_code}")
    cite_body = cite.json()
    print(f"  citations: {len(cite_body.get('citations') or [])}")
    if cite_body.get("expansion"):
        print(f"  expansion queries: {cite_body['expansion'].get('queries')}")

    chat = client.post("/api/chat", json={"message": "理财安全吗？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    print(f"  chat citations: {len(chat_body.get('citations') or [])}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
