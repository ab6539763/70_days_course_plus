# expansion_api 脚本精读

## expansion_api_demo.py 全文

```python
"""
Expansion API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day35/expansion_api_demo.py
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

    print("=== Day 35 Expansion API Demo ===\n")
    cfg = client.get("/api/knowledge/expansion-config").json()
    print(f"  enabled={cfg.get('enabled')} mode={cfg.get('mode')} max={cfg.get('max_queries')}")

    preview = client.post(
        "/api/knowledge/expansion-preview",
        json={"query": "理财安全吗"},
    )
    print(f"  expansion-preview: {preview.status_code}")
    body = preview.json()
    print(f"  queries: {body.get('queries')}")

    cite = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "理财安全吗"},
    )
    print(f"  citation-preview: {cite.status_code}")
    cite_body = cite.json()
    print(f"  citations: {len(cite_body.get('citations') or [])}")
    if cite_body.get("expansion"):
        print(f"  expansion queries: {cite_body['expansion'].get('queries')}")

    chat = client.post("/api/chat", json={"message": "理财安全吗？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    print(f"  chat citations: {len(chat_body.get('citations') or [])}")
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
| L42–L44 | chat + health version `v0.35.0` |

---

## expansion_demo.py 全文

```python
"""
多查询扩展演示 — 单问句 → 多路 query → 合并 citations

运行：PYTHONPATH=src python3 src/day35/expansion_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day35.constants import EXPANSION_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.query_expander import build_expander


def main() -> int:
    print("=" * 60)
    print("  Day 35 Query Expansion 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_expansion_config()
    expander = build_expander(cfg)
    print(f"\n  expansion enabled={cfg.enabled} mode={cfg.mode} max={cfg.max_queries}")

    for item in EXPANSION_QUERIES:
        q = item["query"]
        exp = expander.expand(q)
        print(f"\n  Q: {q}")
        print(f"    queries ({len(exp.queries)}): {list(exp.queries)}")
        data = store.fetch_citations(q)
        cites = data.get("citations") or []
        print(f"    merged citations: {len(cites)}")
        if cites:
            print(f"    top1: {cites[0]['source']} score={cites[0]['score']:.2f}")

    print("\n  ✅ Expansion 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
EXPANSION_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day35/expansion_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day35/expansion_api_demo.py
pytest tests/day35/test_expansion_api.py -v
```
