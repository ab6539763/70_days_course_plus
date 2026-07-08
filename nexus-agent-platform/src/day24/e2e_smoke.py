"""
Sprint 3 E2E 冒烟 — TestClient 模拟投资人三问句

运行：NEXUS_LLM_MOCK=1 python3 src/day24/e2e_smoke.py
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
from day24.constants import DEMO_QUERIES


def run_smoke() -> int:
    client = TestClient(create_app())
    print("=== Sprint 3 E2E 冒烟 ===\n")

    health = client.get("/api/health")
    if health.status_code != 200:
        print(f"  ❌ health {health.status_code}")
        return 1
    print(f"  ✅ health {health.json()}")

    index = client.get("/")
    if "NexusAgent" not in index.text:
        print("  ❌ 首页未加载")
        return 1
    print("  ✅ frontend index")

    for script in ("session.js", "errors.js", "config.js"):
        r = client.get(f"/{script}")
        if r.status_code != 200:
            print(f"  ❌ {script} 缺失")
            return 1
    print("  ✅ session.js / errors.js / config.js")

    sid = "e2e-demo-session"
    kinds = set()
    for q in DEMO_QUERIES:
        resp = client.post("/api/chat", json={"message": q, "session_id": sid})
        if resp.status_code != 200:
            print(f"  ❌ chat failed: {q} -> {resp.status_code}")
            return 1
        data = resp.json()
        kinds.add(data.get("kind"))
        print(f"  ✅ Q: {q[:20]}… kind={data.get('kind')}")

    reset = client.post("/api/session/reset", json={"session_id": sid})
    if reset.status_code != 200:
        print("  ❌ session reset failed")
        return 1
    print("  ✅ session reset")

    print(f"\n  命中 kind 集合: {sorted(kinds)}")
    print("  E2E 冒烟完成")
    return 0


def main() -> int:
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
