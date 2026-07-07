"""
投资人演示脚本 — 终端输出版

运行：NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_demo.py
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


def main() -> int:
    client = TestClient(create_app())
    print("=" * 58)
    print("  NexusAgent Sprint 3 投资人演示（脚本预演）")
    print("=" * 58)

    h = client.get("/api/health").json()
    print(f"\n[1/4] 健康检查: status={h['status']} version={h['version']} mock_llm={h['mock_llm']}")

    print("\n[2/4] 三问句对话:")
    sid = "investor-demo"
    for i, q in enumerate(DEMO_QUERIES, 1):
        r = client.post("/api/chat", json={"message": q, "session_id": sid})
        d = r.json()
        print(f"  {i}. {q}")
        print(f"     → [{d['kind']}] {d['reply'][:70]}…")

    print("\n[3/4] 前端资源:")
    for f in ("index.html", "app.js", "session.js"):
        ok = client.get(f"/{f}").status_code == 200
        print(f"  {'✅' if ok else '❌'} {f}")

    print("\n[4/4] 演示提示:")
    print("  启动: PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py --serve")
    print("  浏览器: http://127.0.0.1:8000")
    print("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
