"""
MCP API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day44/mcp_api_demo.py
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

    print("=== Day 44 MCP API Demo ===\n")
    cfg = client.get("/api/agent/mcp-config").json()
    print(f"  server_name={cfg.get('server_name')} enabled={cfg.get('enabled')}")

    listed = client.post("/api/agent/mcp-list-tools", json={})
    print(f"  mcp-list-tools: {listed.status_code}")
    list_body = listed.json()
    print(f"  tools={[t.get('name') for t in list_body.get('tools', [])]}")

    preview = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  mcp-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} mcp_tools={body.get('mcp_tools')}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    print(f"  chat mcp_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} mcp_tools={chat_body.get('mcp_tools')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
