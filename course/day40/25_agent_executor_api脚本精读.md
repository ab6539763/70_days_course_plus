# Day 40 API 脚本精读

## API demo 全文

```python
"""
AgentExecutor API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day40/executor_api_demo.py
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

    print("=== Day 40 AgentExecutor API Demo ===\n")
    cfg = client.get("/api/agent/executor-config").json()
    print(f"  max_iterations={cfg.get('max_iterations')} enabled={cfg.get('enabled')}")

    preview = client.post(
        "/api/agent/executor-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  executor-preview: {preview.status_code}")
    body = preview.json()
    print(f"  tools_used={body.get('tools_used')} steps={len(body.get('steps', []))}")
    print(f"  intermediate_steps={len(body.get('intermediate_steps', []))}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "executor_mode": True},
    )
    print(f"  chat executor_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} tools={chat_body.get('tools_used')}")
    print(f"  executor_trace steps={len(chat_body.get('executor_trace') or [])}")
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
| chat + health | 端到端 + 版本号 `v0.40.0` |

---

## CLI demo 全文

```python
"""
AgentExecutor + StructuredTool 演示

运行：PYTHONPATH=src python3 src/day40/executor_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.agent_executor import AgentExecutor
from agent.executor_config import ExecutorConfig
from agent.structured_tool import StructuredTool, tool, tools_to_openai_schema
from api.factory import create_orchestrator
from day40.constants import EXECUTOR_CASES


@tool(name="echo_ping", description="回显测试输入")
def echo_ping(text: str) -> str:
    return f"echo: {text}"


def main() -> int:
    print("=" * 60)
    print("  Day 40 AgentExecutor + StructuredTool 演示")
    print("=" * 60)

    orchestrator = create_orchestrator()
    executor = AgentExecutor.from_executor(
        orchestrator.tool_executor,
        config=ExecutorConfig(enabled=True, max_iterations=3),
    )

    print(f"\n  已注册 StructuredTool: {len(executor.tools)} 个")
    schemas = tools_to_openai_schema(executor.tools[:3])
    print(f"  OpenAI schema 样例: {schemas[0]['function']['name']}")

    demo_tool = echo_ping
    assert isinstance(demo_tool, StructuredTool)
    print(f"  @tool 装饰器: {demo_tool.run({'text': 'hello'})}")

    for item in EXECUTOR_CASES:
        q = item["query"]
        outcome = executor.invoke(q)
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        flag = "✅" if tool == item["expect_tool"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    tools={list(outcome.tools_used)} steps={len(outcome.steps)} {flag}")
        print(f"    reply: {outcome.reply[:80]}...")
        for step in outcome.steps:
            if step.action:
                obs = (step.observation or "")[:60]
                print(f"      step{step.step}: {step.action} → {obs}...")

    print("\n  ✅ AgentExecutor 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## constants.py（case studies，query / 预期工具）

```python
CASES = (
    ("运营要求新增「工单查询」工具", "..."),
    ("工具入参类型不对", "..."),
    ("同一问题分别跑 Day39/Day40", "..."),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day40/executor_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day40/executor_api_demo.py
pytest tests/day40/ -v
```
