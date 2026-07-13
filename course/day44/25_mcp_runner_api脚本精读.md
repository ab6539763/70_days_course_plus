# Day 44 API 脚本精读

## API demo 全文

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
| 开头 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| TestClient | 创建 app 与测试客户端 |
| bootstrap | 保证语料/知识库已初始化 |
| GET 配置 | 读默认配置 |
| PUT 配置 | 更新配置 — **API 核心演示** |
| status | 对账 config 是否写回 store |
| chat + health | 端到端 + 版本号 `v0.44.0` |

---

## CLI demo 全文

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


---

## constants.py（case studies，query / 预期工具）

```python
CASES = (
    ("「客服电话多少」", "..."),
    ("「年化收益怎么样」", "..."),
    ("把 NexusMcpServer 换成外部进程/HTTP MCP 端点", "..."),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day44/mcp_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day44/mcp_api_demo.py
pytest tests/day44/ -v
```
