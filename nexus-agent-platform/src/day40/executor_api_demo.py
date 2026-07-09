"""
AgentExecutor API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day40/executor_api_demo.py
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

    print("=== Day 40 AgentExecutor API Demo ===\n")
    cfg = client.get("/api/agent/executor-config").json()
    print(f"  max_iterations={cfg.get('max_iterations')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/executor-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  executor-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} steps={len(body.get('steps', []))}")
    print(f"  intermediate_steps={len(body.get('intermediate_steps', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "executor_mode": True},
    )
    print(f"  chat executor_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} tools={chat_body.get('tools_used')}")
    print(f"  executor_trace steps={len(chat_body.get('executor_trace') or [])}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
