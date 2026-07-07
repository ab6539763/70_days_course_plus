"""
HTTP 与 urllib 基础演示

运行：python3 src/day12/http_demos.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def demo_urlopen_get() -> None:
    print("=== urllib GET 示例（httpbin.org）===\n")
    url = "https://httpbin.org/get?demo=nexus"
    req = urllib.request.Request(url, headers={"User-Agent": "NexusAgent/0.1"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print("状态码字段 args:", data.get("args"))


def demo_request_headers() -> None:
    print("\n=== 请求头组装 ===\n")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-***",
    }
    for k, v in headers.items():
        print(f"  {k}: {v}")


def main() -> int:
    try:
        demo_urlopen_get()
    except Exception as exc:
        print(f"  ⚠️  网络演示跳过（离线环境）: {exc}")
    demo_request_headers()
    return 0


if __name__ == "__main__":
    sys.exit(main())
