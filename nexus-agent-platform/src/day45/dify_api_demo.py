"""
Dify API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day45/dify_api_demo.py
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

    print("=== Day 45 Dify API Demo ===\n")
    cfg = client.get("/api/agent/dify-config").json()
    print(f"  workflow_name={cfg.get('workflow_name')} enabled={cfg.get('enabled')}")

    exported = client.post("/api/agent/dify-export", json={})
    print(f"  dify-export: {exported.status_code}")
    export_body = exported.json()
    node_ids = [n.get("id") for n in export_body.get("workflow", {}).get("graph", {}).get("nodes", [])]
    print(f"  nodes={node_ids}")

    preview = client.post(
        "/api/agent/dify-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  dify-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} dify_trace 节点数={len(body.get('dify_trace', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "dify_mode": True},
    )
    print(f"  chat dify_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} dify_trace 节点数={len(chat_body.get('dify_trace') or [])}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
