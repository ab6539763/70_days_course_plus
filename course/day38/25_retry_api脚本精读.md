# route_api 脚本精读

## route_api_demo.py 全文

```python
"""
Validation Retry API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day38/retry_api_demo.py
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

    print("=== Day 38 Validation Retry API Demo ===\n")
    cfg = client.get("/api/knowledge/validation-config").json()
    print(f"  retry_on_fail={cfg.get('retry_on_fail')} max_retries={cfg.get('max_retries')}")

    preview = client.post(
        "/api/knowledge/validation-retry-preview",
        json={
            "query": "客服电话多少",
            "reply": "请拨打客服热线 400-888-1234。",
        },
    )
    print(f"  validation-retry-preview: {preview.status_code}")
    body = preview.json()
    print(f"  retries={body.get('retries')} passed={body.get('passed')}")

    client.put(
        "/api/knowledge/validation-config",
        json={
            "enabled": True,
            "mode": "overlap",
            "min_score": 0.35,
            "refuse_on_fail": True,
            "retry_on_fail": True,
            "max_retries": 1,
        },
    )
    chat = client.post("/api/chat", json={"message": "根据资料查询年化收益率"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    val = chat_body.get("validation") or {}
    print(f"  validation retries={val.get('retries')} passed={val.get('passed')}")
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
| L42–L44 | chat + health version `v0.38.0` |

---

## route_demo.py 全文

```python
"""
多轮 Self-RAG 重试演示 — 校验失败后 rag_wide 重检索

运行：PYTHONPATH=src python3 src/day38/retry_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day38.constants import RETRY_CASES
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import ValidationConfig
from rag.validation_retry import apply_validation_retry


def main() -> int:
    print("=" * 60)
    print("  Day 38 多轮 Self-RAG 重试演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_validation_config(
        ValidationConfig(
            enabled=True,
            min_score=0.35,
            refuse_on_fail=False,
            retry_on_fail=True,
            max_retries=1,
        )
    )

    for item in RETRY_CASES:
        q = item["query"]
        reply = item["reply"]
        cite_data = store.fetch_citations(q)
        citations = cite_data.get("citations") or []
        outcome = apply_validation_retry(store, q, reply, citations, cite_data)
        assert outcome is not None
        flag = "✅" if outcome.validation.passed == item["expect_passed_after_retry"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    retries={outcome.validation.retries} passed={outcome.validation.passed} {flag}")
        print(f"    reason: {outcome.validation.reason}")
        route = outcome.cite_data.get("route")
        if route:
            print(f"    route: {route.get('intent')} expand={route.get('expand')}")

    print("\n  ✅ Retry 演示完成")
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
PYTHONPATH=src python3 src/day38/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day38/route_api_demo.py
pytest tests/day38/test_route_api.py -v
```
