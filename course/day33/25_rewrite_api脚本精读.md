# rewrite_api 脚本精读

## rewrite_api_demo.py 全文

```python
"""
Query Rewrite API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day33/rewrite_api_demo.py
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

    print("=== Day 33 Rewrite API Demo ===\n")
    cfg = client.get("/api/knowledge/rewrite-config").json()
    print(f"  enabled={cfg.get('enabled')} mode={cfg.get('mode')}")

    preview = client.post(
        "/api/knowledge/rewrite-preview",
        json={"query": "那个理财能赚多少"},
    )
    print(f"  preview: {preview.status_code} → {preview.json().get('rewritten')}")

    resp = client.put(
        "/api/knowledge/rewrite-config",
        json={
            "enabled": True,
            "mode": "rules",
            "fallback_to_original": True,
            "max_rewrite_len": 200,
        },
    )
    print(f"  PUT rewrite-config: {resp.status_code}")

    chat = client.post("/api/chat", json={"message": "那个理财能赚多少？"})
    print(f"  chat: {chat.status_code}")
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
| L39–L40 | status 对账 rewrite_config |
| L42–L44 | chat + health version `v0.33.0` |

---

## rewrite_demo.py 全文

```python
"""
查询改写演示 — 对比关闭 / 开启规则改写

运行：PYTHONPATH=src python3 src/day33/rewrite_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day33.constants import REWRITE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever


def _preview(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rewrite_config(RewriteConfig(enabled=enabled))
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if not isinstance(retriever, RewritingRetriever):
        raise RuntimeError("expected RewritingRetriever")
    retriever.search(query, top_k=1)
    rw = retriever.last_rewrite
    if not rw:
        return "—"
    label = "rewrite" if enabled else "passthrough"
    return f"[{label}] {rw.rewritten!r} (rule={rw.rule_id or '—'})"


def main() -> int:
    print("=" * 60)
    print("  Day 33 Query Rewrite 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rewrite_config()
    print(f"\n  默认 rewrite: enabled={cfg.enabled} mode={cfg.mode}")

    for item in REWRITE_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭改写 → {_preview(store, q, enabled=False)}")
        print(f"    开启改写 → {_preview(store, q, enabled=True)}")

    print("\n  ✅ Query Rewrite 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
RERANK_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day33/rewrite_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day33/rewrite_api_demo.py
pytest tests/day33/test_rewrite_api.py -v
```
