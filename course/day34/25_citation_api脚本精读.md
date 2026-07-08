# citation_api 脚本精读

## citation_api_demo.py 全文

```python
"""
Citation API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day34/citation_api_demo.py
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

    print("=== Day 34 Citation API Demo ===\n")
    cfg = client.get("/api/knowledge/citation-config").json()
    print(f"  enabled={cfg.get('enabled')} max={cfg.get('max_citations')}")

    preview = client.post(
        "/api/knowledge/citation-preview",
        json={"query": "那个理财能赚多少"},
    )
    print(f"  citation-preview: {preview.status_code}")
    cites = preview.json().get("citations") or []
    print(f"  citations count: {len(cites)}")
    if cites:
        print(f"  top1 source: {cites[0].get('source')}")

    chat = client.post("/api/chat", json={"message": "年化收益率是多少？"})
    print(f"  chat: {chat.status_code}")
    body = chat.json()
    print(f"  chat citations: {len(body.get('citations') or [])}")
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
| L42–L44 | chat + health version `v0.34.0` |

---

## citation_demo.py 全文

```python
"""
引用溯源演示 — 检索结果结构化 citations

运行：PYTHONPATH=src python3 src/day34/citation_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day34.constants import CITATION_QUERIES
from rag.knowledge_store import KnowledgeStore


def main() -> int:
    print("=" * 60)
    print("  Day 34 Citation 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_citation_config()
    print(f"\n  citation enabled={cfg.enabled} max={cfg.max_citations}")

    for item in CITATION_QUERIES:
        q = item["query"]
        data = store.fetch_citations(q)
        print(f"\n  Q: {q}")
        if data.get("rewrite") and data["rewrite"].get("changed"):
            print(f"    rewrite: {data['rewrite']['rewritten']!r}")
        for c in data.get("citations") or []:
            print(
                f"    [{c['rank']}] {c['source']} score={c['score']:.2f} "
                f"{c['preview'][:50]}…"
            )

    print("\n  ✅ Citation 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
CITATION_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day34/citation_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day34/citation_api_demo.py
pytest tests/day34/test_citation_api.py -v
```
