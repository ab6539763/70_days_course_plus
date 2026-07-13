# Day 35 API 脚本精读

## API demo 全文

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
| 开头 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| TestClient | 创建 app 与测试客户端 |
| bootstrap | 保证语料/知识库已初始化 |
| GET 配置 | 读默认配置 |
| PUT 配置 | 更新配置 — **API 核心演示** |
| status | 对账 config 是否写回 store |
| chat + health | 端到端 + 版本号 `v0.35.0` |

---

## CLI demo 全文

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


---

## constants.py（case studies，query）

```python
EXPANSION_QUERIES = (
    ("理财安全吗",),
    ("客服电话多少",),
    ("PUT enabled=false",),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day35/expansion_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day35/expansion_api_demo.py
pytest tests/day35/ -v
```
