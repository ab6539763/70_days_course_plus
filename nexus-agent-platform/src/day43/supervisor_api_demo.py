"""
Supervisor API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day43/supervisor_api_demo.py
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

    print("=== Day 43 Supervisor API Demo ===\n")
    cfg = client.get("/api/agent/supervisor-config").json()
    print(f"  max_delegations={cfg.get('max_delegations')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/supervisor-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  supervisor-preview: {preview.status_code}")
    body = preview.json()
    print(f"  delegated_agents={body.get('delegated_agents')} tools={body.get('tools_used')}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "supervisor_mode": True},
    )
    print(f"  chat supervisor_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} delegated={chat_body.get('delegated_agents')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
