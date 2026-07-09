"""
Validation Retry API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day38/retry_api_demo.py
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

    print("=== Day 38 Validation Retry API Demo ===\n")
    cfg = client.get("/api/knowledge/validation-config").json()
    print(f"  retry_on_fail={cfg.get('retry_on_fail')} max_retries={cfg.get('max_retries')}")

    preview = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    print(f"  validation-retry-preview: {preview.status_code}")
    body = preview.json()
    print(f"  retries={body.get('retries')} passed={body.get('passed')}")

    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    chat = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    val = chat_body.get("validation") or {}
    print(f"  validation retries={val.get('retries')} passed={val.get('passed')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
