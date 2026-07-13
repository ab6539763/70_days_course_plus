# Day 41 API 脚本精读

## API demo 全文

```python
"""
StateGraph API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day41/graph_api_demo.py
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

    print("=== Day 41 StateGraph API Demo ===\n")
    cfg = client.get("/api/agent/graph-config").json()
    print(f"  max_iterations={cfg.get('max_iterations')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/graph-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  graph-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} node_path={body.get('node_path')}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "graph_mode": True},
    )
    print(f"  chat graph_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} tools={chat_body.get('tools_used')}")
    print(f"  graph_trace steps={len(chat_body.get('graph_trace') or [])}")
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
| chat + health | 端到端 + 版本号 `v0.41.0` |

---

## CLI demo 全文

```python
"""
StateGraph RAG Agent 演示

运行：PYTHONPATH=src python3 src/day41/graph_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.graph_config import GraphConfig
from agent.rag_agent_graph import RAGAgentGraph
from agent.state_graph import StateGraph
from api.factory import create_orchestrator
from day41.constants import GRAPH_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 41 StateGraph RAG Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    graph = RAGAgentGraph.from_executor(
        orchestrator.tool_executor,
        config=GraphConfig(enabled=True, max_iterations=3),
    )

    print(f"\n  编译图节点: planner → tool_runner → answer")
    print(f"  StateGraph API: add_node / add_edge / add_conditional_edges / compile")

    for item in GRAPH_CASES:
        q = item["query"]
        outcome = graph.invoke(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    node_path={list(outcome.node_path)} tools={list(outcome.tools_used)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.node:
                print(f"      step{step.step} [{step.node}]: {step.thought[:50]}...")

    print("\n  ✅ StateGraph 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## constants.py（case studies，query / 预期工具）

```python
CASES = (
    ("合规要求记录每一步决策节点", "..."),
    ("简单问题不需要工具", "..."),
    ("Day42 需要在工具执行后插入人工审批", "..."),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day41/graph_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day41/graph_api_demo.py
pytest tests/day41/ -v
```
