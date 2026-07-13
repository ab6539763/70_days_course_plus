# Day 36 API 脚本精读

## API demo 全文

```python
"""
Route API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day36/route_api_demo.py
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

    print("=== Day 36 Route API Demo ===\n")
    cfg = client.get("/api/knowledge/route-config").json()
    print(f"  enabled={cfg.get('enabled')} fallback={cfg.get('fallback_intent')}")

    preview = client.post(
        "/api/knowledge/route-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  route-preview: {preview.status_code}")
    body = preview.json()
    print(f"  intent={body.get('intent')} expand={body.get('expand')}")

    cite = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "客服电话多少"},
    )
    print(f"  citation-preview: {cite.status_code}")
    cite_body = cite.json()
    if cite_body.get("route"):
        print(f"  route: {cite_body['route'].get('intent')}")

    chat = client.post("/api/chat", json={"message": "理财安全吗？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    if chat_body.get("route"):
        print(f"  chat route: {chat_body['route'].get('intent')}")
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
| chat + health | 端到端 + 版本号 `v0.36.0` |

---

## CLI demo 全文

```python
"""
检索管线路由演示 — 意图 → expand/rewrite 开关

运行：PYTHONPATH=src python3 src/day36/route_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day36.constants import ROUTE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.query_router import RuleBasedQueryRouter


def main() -> int:
    print("=" * 60)
    print("  Day 36 Query Router 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_route_config()
    router = RuleBasedQueryRouter(config=cfg)
    print(f"\n  route enabled={cfg.enabled} fallback={cfg.fallback_intent}")

    for item in ROUTE_QUERIES:
        q = item["query"]
        route = router.route(q)
        print(f"\n  Q: {q}")
        print(f"    intent={route.intent} expand={route.expand} rewrite={route.rewrite}")
        print(f"    label: {route.label}")
        data = store.fetch_citations(q)
        if data.get("route"):
            print(f"    routed expand={data['route']['expand']}")

    print("\n  ✅ Route 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## constants.py（case studies，query）

```python
ROUTE_QUERIES = (
    ("客服电话多少",),
    ("年化收益怎么样",),
    ("理财安全吗",),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day36/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day36/route_api_demo.py
pytest tests/day36/ -v
```
