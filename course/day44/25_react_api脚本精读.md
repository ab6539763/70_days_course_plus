# route_api 脚本精读

## route_api_demo.py 全文

```python
"""
MCP API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day44/mcp_api_demo.py
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

    print("=== Day 44 MCP API Demo ===\n")
    cfg = client.get("/api/agent/mcp-config").json()
    print(f"  server_name={cfg.get('server_name')} enabled={cfg.get('enabled')}")

    listed = client.post("/api/agent/mcp-list-tools", json={})
    print(f"  mcp-list-tools: {listed.status_code}")
    list_body = listed.json()
    print(f"  tools={[t.get('name') for t in list_body.get('tools', [])]}")

    preview = client.post(
        "/api/agent/mcp-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  mcp-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} mcp_tools={body.get('mcp_tools')}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "mcp_mode": True},
    )
    print(f"  chat mcp_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} mcp_tools={chat_body.get('mcp_tools')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| L13–L17 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| L21–L22 | TestClient 与 app |
| L26 | bootstrap 保证语料 |
| L30–L31 | GET 默认 rewrite 配置 |
| L33–L37 | PUT pool=20 — **API 核心演示** |
| L39–L40 | status 对账 citation_config |
| L42–L44 | chat + health version `v0.44.0` |

---

## route_demo.py 全文

```python
"""
MCP 工具桥接演示

运行：PYTHONPATH=src python3 src/day44/mcp_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.mcp_config import McpConfig
from agent.mcp_runner import McpRunner
from api.factory import create_orchestrator
from day44.constants import MCP_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 44 MCP 工具桥接演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    runner = McpRunner.from_executor(
        orchestrator.tool_executor,
        config=McpConfig(enabled=True),
    )

    tools = runner.list_tools()
    print(f"\n  MCP Server 工具: {tools}")
    for item in MCP_CASES:
        outcome = runner.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    mcp_tools={list(outcome.mcp_tools)} tools_used={list(outcome.tools_used)} {flag}")
        print(f"    reply: {outcome.reply[:70]}...")

    print("\n  ✅ MCP 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
ROUTE_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day37/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/route_api_demo.py
pytest tests/day37/test_route_api.py -v
```
