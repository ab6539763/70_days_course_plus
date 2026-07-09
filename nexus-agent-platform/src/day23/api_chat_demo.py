"""
API Chat 端点演示 — TestClient 无网络

运行：NEXUS_LLM_MOCK=1 python3 src/day23/api_chat_demo.py
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

QUERIES = [
    "投资有风险吗",
    "根据资料，年化收益率是多少？",
    "帮我总结要点",
]


def main() -> int:
    client = TestClient(create_app())
    print("=== POST /api/chat 演示 ===\n")

    for q in QUERIES:
        resp = client.post("/api/chat", json={"message": q})
        data = resp.json()
        print(f"  Q: {q}")
        print(f"  kind={data.get('kind')} meta={data.get('meta')}")
        print(f"  reply: {data.get('reply', '')[:90]}...")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
