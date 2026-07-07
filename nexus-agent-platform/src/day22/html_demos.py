"""
HTML/CSS 结构演示说明

运行：python3 src/day22/html_demos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent.parent
_FRONTEND = _REPO / "frontend"


def main() -> int:
    print("=== Day 22 前端文件清单 ===\n")
    for path in sorted(_FRONTEND.glob("*")):
        if path.is_file():
            size = path.stat().st_size
            print(f"  {path.name:16} {size:6} bytes")

    html = (_FRONTEND / "index.html").read_text(encoding="utf-8")
    print(f"\n  index.html 行数: {len(html.splitlines())}")
    print(f"  标题包含 NexusAgent: {'NexusAgent' in html}")
    print("\n  本地预览: cd frontend && python3 -m http.server 8080")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
