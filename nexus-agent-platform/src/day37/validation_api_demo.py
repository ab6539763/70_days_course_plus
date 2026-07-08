"""
Validation API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/validation_api_demo.py
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

    print("=== Day 37 Validation API Demo ===\n")
    cfg = client.get("/api/knowledge/validation-config").json()
    print(f"  enabled={cfg.get('enabled')} min_score={cfg.get('min_score')}")

    preview = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "年化收益怎么样",
            "reply": "今天北京天气晴朗，适合出游。",
        },
    )
    print(f"  validation-preview: {preview.status_code}")
    body = preview.json()
    print(f"  passed={body.get('passed')} score={body.get('score')}")

    chat = client.post("/api/chat", json={"message": "客服电话多少？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    if chat_body.get("validation"):
        print(f"  validation passed={chat_body['validation'].get('passed')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
