"""
Route API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day36/route_api_demo.py
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

    print("=== Day 36 Route API Demo ===\n")
    cfg = client.get("/api/knowledge/route-config").json()
    print(f"  enabled={cfg.get('enabled')} fallback={cfg.get('fallback_intent')}")

    preview = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  route-preview: {preview.status_code}")
    body = preview.json()
    print(f"  intent={body.get('intent')} expand={body.get('expand')}")

    cite = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  citation-preview: {cite.status_code}")
    cite_body = cite.json()
    if cite_body.get("route"):
        print(f"  route: {cite_body['route'].get('intent')}")

    chat = client.post("/api/chat", json={"message": "理财安全吗？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    if chat_body.get("route"):
        print(f"  chat route: {chat_body['route'].get('intent')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
