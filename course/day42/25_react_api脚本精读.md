# route_api 脚本精读

## route_api_demo.py 全文

```python
"""
人工审批 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day42/approval_api_demo.py
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

    print("=== Day 42 Approval API Demo ===\n")
    cfg = client.get("/api/agent/approval-config").json()
    print(f"  mock_auto_approve={cfg.get('mock_auto_approve')}")

    preview = client.post(
        "/api/agent/approval-preview",
        json={"query": "年化收益怎么样"},
    )
    print(f"  approval-preview: {preview.status_code}")
    body = preview.json()
    print(f"  status={body.get('approval_status')} interrupted={body.get('interrupted')}")

    chat = client.post(
        "/api/chat",
        json={"message": "理财安全吗", "approval_mode": True},
    )
    print(f"  chat approval_mode: {chat.status_code}")
    chat_body = chat.json()
    print(f"  kind={chat_body.get('kind')} approval={chat_body.get('approval')}")
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
| L42–L44 | chat + health version `v0.42.0` |

---

## route_demo.py 全文

```python
"""
人工审批工作流演示

运行：PYTHONPATH=src python3 src/day42/approval_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent.approval_checkpoint import approval_checkpoint_store
from agent.approval_config import ApprovalConfig
from agent.approval_workflow_graph import ApprovalWorkflowGraph
from agent.graph_config import ApprovalConfig
from api.factory import create_orchestrator
from day42.constants import APPROVAL_CASES


def main() -> int:
    print("=" * 60)
    print("  Day 42 人工审批工作流演示")
    print("=" * 60)

    approval_checkpoint_store.clear()
    orchestrator = create_orchestrator()

    # mock 自动审批
    workflow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        graph_config=ApprovalConfig(max_iterations=3),
        approval_config=ApprovalConfig(mock_auto_approve=True),
    )
    for item in APPROVAL_CASES:
        outcome = workflow.invoke(item["query"])
        tool = outcome.tools_used[0] if outcome.tools_used else "none"
        has_approval = "human_approval" in outcome.checkpoint_id
        print(f"\n  Q: {item['query']}")
        print(f"    checkpoint_id={list(outcome.checkpoint_id)} approval={outcome.approval_status}")
        print(f"    tools={list(outcome.tools_used)} {tool} interrupted={outcome.interrupted}")

    # 中断 + 恢复
    print("\n  --- 中断恢复演示 ---")
    interrupt_flow = ApprovalWorkflowGraph.from_executor(
        orchestrator.tool_executor,
        approval_config=ApprovalConfig(mock_auto_approve=False),
    )
    pending = interrupt_flow.invoke("年化收益怎么样")
    print(f"  interrupted={pending.interrupted} checkpoint={pending.checkpoint_id}")
    if pending.checkpoint_id:
        resumed = interrupt_flow.resume(pending.checkpoint_id, approved=True, comment="合规通过")
        print(f"  resumed reply: {resumed.reply[:80]}...")
        print(f"  status={resumed.approval_status}")

    print("\n  ✅ 审批工作流演示完成")
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
