"""
API 健康检查演示

运行：python3 src/day23/api_health_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi.testclient import TestClient

from api.app import create_app


def main() -> int:
    client = TestClient(create_app())
    resp = client.get("/api/health")
    print("=== API Health ===\n")
    print(f"  status: {resp.status_code}")
    print(f"  body: {resp.json()}")
    return 0 if resp.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
