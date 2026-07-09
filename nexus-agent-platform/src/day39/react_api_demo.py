"""
ReAct Agent API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day39/react_api_demo.py
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

    print("=== Day 39 ReAct API Demo ===\n")
    cfg = client.get("/api/agent/react-config").json()
    print(f"  max_steps={cfg.get('max_steps')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/react-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  react-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} steps={len(body.get('steps', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "agent_mode": True},
    )
    print(f"  chat agent_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} tools={chat_body.get('tools_used')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
