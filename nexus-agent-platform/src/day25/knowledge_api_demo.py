"""
知识库 API 演示 — TestClient

运行：
    cd nexus-agent-platform
    PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day25/knowledge_api_demo.py
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from fastapi.testclient import TestClient

from api.app import create_app
from day25.constants import SAMPLE_UPLOAD_NAME, SAMPLE_UPLOAD_TEXT
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


def main() -> int:
    store = KnowledgeStore.bootstrap_from_sample_docs()
    set_knowledge_store(store)

    client = TestClient(create_app())
    print("=== Day 25 Knowledge API Demo ===\n")

    status = client.get("/api/knowledge/status")
    print(f"  GET /status → {status.json()}")

    files = {"file": (SAMPLE_UPLOAD_NAME, io.BytesIO(SAMPLE_UPLOAD_TEXT.encode("utf-8")), "text/plain")}
    upload = client.post("/api/knowledge/upload", files=files)
    print(f"\n  POST /upload → {upload.json()}")

    chat = client.post(
        "/api/chat",
        json={"message": "最低起购金额是多少", "session_id": "kb-demo"},
    )
    print(f"\n  POST /chat → kind={chat.json().get('kind')}")
    print(f"  reply: {chat.json().get('reply', '')[:120]}…")

    health = client.get("/api/health")
    print(f"\n  GET /health version={health.json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
