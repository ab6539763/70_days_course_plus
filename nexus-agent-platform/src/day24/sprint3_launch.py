"""
Sprint 3 统一启动与冒烟检查

运行：
    cd nexus-agent-platform
    PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day24/sprint3_launch.py

加 --serve 启动 uvicorn（阻塞）
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
_PLATFORM = _SRC.parent
_REPO = _PLATFORM.parent

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def run_pytest() -> int:
    print("▶ pytest day22 + day23 + day24 …")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/day22/", "tests/day23/", "tests/day24/", "-q"],
        cwd=_PLATFORM,
        env={**os.environ, "PYTHONPATH": str(_SRC), "NEXUS_LLM_MOCK": "1"},
    )
    return proc.returncode


def run_smoke() -> int:
    os.environ.setdefault("NEXUS_LLM_MOCK", "1")
    from day24.e2e_smoke import run_smoke as _smoke

    return _smoke()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sprint 3 统一启动与冒烟")
    parser.add_argument("--serve", action="store_true", help="通过检查后启动 uvicorn")
    parser.add_argument("--skip-pytest", action="store_true")
    args = parser.parse_args(argv)

    print("=" * 56)
    print("  NexusAgent Sprint 3 Launch (Day 24)")
    print("=" * 56)

    if not args.skip_pytest:
        if run_pytest() != 0:
            print("\n❌ pytest 未通过，中止启动")
            return 1
        print("✅ pytest 通过\n")

    if run_smoke() != 0:
        print("\n❌ E2E 冒烟未通过")
        return 1
    print("✅ E2E 冒烟通过\n")

    print("  浏览器访问: http://127.0.0.1:8000")
    print("  Mock 预览:  http://127.0.0.1:8000/?mock=1")
    print("=" * 56)

    if args.serve:
        import uvicorn

        uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
