# route_api 脚本精读

## route_api_demo.py 全文

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
| L13–L17 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| L21–L22 | TestClient 与 app |
| L26 | bootstrap 保证语料 |
| L30–L31 | GET 默认 rewrite 配置 |
| L33–L37 | PUT pool=20 — **API 核心演示** |
| L39–L40 | status 对账 citation_config |
| L42–L44 | chat + health version `v0.36.0` |

---

## route_demo.py 全文

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
PYTHONPATH=src python3 src/day36/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day36/route_api_demo.py
pytest tests/day36/test_route_api.py -v
```
