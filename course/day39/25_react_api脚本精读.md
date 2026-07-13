# Day 39 API 脚本精读

## API demo 全文

```python
"""
ReAct Agent API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day39/react_api_demo.py
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

    print("=== Day 39 ReAct API Demo ===\n")
    cfg = client.get("/api/agent/react-config").json()
    print(f"  max_steps={cfg.get('max_steps')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/react-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  react-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} steps={len(body.get('steps', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "agent_mode": True},
    )
    print(f"  chat agent_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} tools={chat_body.get('tools_used')}")
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
| chat + health | 端到端 + 版本号 `v0.39.0` |

---

## CLI demo 全文

```python
"""
手写 ReAct Agent 演示

运行：PYTHONPATH=src python3 src/day39/react_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.react_agent import ReActAgent
from agent.react_config import ReactConfig
from api.factory import create_orchestrator
from day39.constants import REACT_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 39 手写 ReAct Agent 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    agent = ReActAgent(
        orchestrator.tool_executor,
        config=ReactConfig(enabled=True, max_steps=3),
    )

    for item in REACT_CASES:
        q = item["query"]
        outcome = agent.run(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    tools={list(outcome.tools_used)} steps={len(outcome.steps)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.action:
                print(f"      step{step.step}: {step.action} → {step.observation[:60]}...")

    print("\n  ✅ ReAct 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## constants.py（case studies，query / 预期工具）

```python
CASES = (
    ("用户先问「客服电话」再问「收益率」", "..."),
    ("Thought 选中一个未注册工具名", "..."),
    ("max_steps=3 但问题需要 4 步", "..."),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day39/react_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day39/react_api_demo.py
pytest tests/day39/ -v
```
