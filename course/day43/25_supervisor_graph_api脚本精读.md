# Day 43 API 脚本精读

## API demo 全文

```python
"""
Supervisor API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day43/supervisor_api_demo.py
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

    print("=== Day 43 Supervisor API Demo ===\n")
    cfg = client.get("/api/agent/supervisor-config").json()
    print(f"  max_delegations={cfg.get('max_delegations')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/supervisor-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  supervisor-preview: {preview.status_code}")
    body = preview.json()
    print(f"  delegated_agents={body.get('delegated_agents')} tools={body.get('tools_used')}")

    chat = client.post(
        "/api/chat",
        json={"message": "客服电话多少", "supervisor_mode": True},
    )
    print(f"  chat supervisor_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} delegated={chat_body.get('delegated_agents')}")
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
| chat + health | 端到端 + 版本号 `v0.43.0` |

---

## CLI demo 全文

```python
"""
Supervisor 多 Agent 演示

运行：PYTHONPATH=src python3 src/day43/supervisor_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.sub_agent import SUB_AGENTS
from agent.supervisor_config import SupervisorConfig
from agent.supervisor_graph import SupervisorGraph
from api.factory import create_orchestrator
from day43.constants import SUPERVISOR_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 43 Supervisor 多 Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    graph = SupervisorGraph.from_executor(
        orchestrator.tool_executor,
        config=SupervisorConfig(enabled=True),
    )

    print(f"\n  子 Agent: {[s.name for s in SUB_AGENTS]}")
    for item in SUPERVISOR_CASES:
        outcome = graph.invoke(item["query"])
        agent = outcome.delegated_agents[-1] if outcome.delegated_agents else "none"
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if agent == item["expect_agent"] else "⚠️"
        print(f"\n  Q: {item['query']}")
        print(f"    delegated={list(outcome.delegated_agents)} node_path={list(outcome.node_path)} {flag}")
        print(f"    tools={list(outcome.tools_used)} reply: {outcome.reply[:70]}...")

    print("\n  ✅ Supervisor 演示完成")
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
    ("「帮我总结一下理财产品」", "..."),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day43/supervisor_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day43/supervisor_api_demo.py
pytest tests/day43/ -v
```
