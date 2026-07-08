"""
启动 FastAPI 开发服务器（教学用）

运行：
    cd nexus-agent-platform
    PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day23/run_server.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")


def main() -> int:
    import uvicorn

    print("NexusAgent API → http://127.0.0.1:8000")
    print("frontend 静态页同源托管，API 模式默认开启")
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
