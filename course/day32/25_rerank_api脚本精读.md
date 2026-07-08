# rerank_api 脚本精读

## rerank_api_demo.py 全文

```python
"""
Rerank API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
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

    print("=== Day 32 Rerank API Demo ===\n")
    cfg = client.get("/api/knowledge/rerank-config").json()
    print(f"  enabled={cfg.get('enabled')} pool={cfg.get('candidate_pool')}")

    resp = client.put(
        "/api/knowledge/rerank-config",
        json={"enabled": True, "candidate_pool": 20, "model": "mock"},
    )
    print(f"  PUT rerank-config: {resp.status_code}")

    status = client.get("/api/knowledge/status").json()
    print(f"  rerank enabled: {status.get('rerank_config', {}).get('enabled')}")

    chat = client.post("/api/chat", json={"message": "年化收益率是多少？"})
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
| L30–L31 | GET 默认 rerank 配置 |
| L33–L37 | PUT pool=20 — **API 核心演示** |
| L39–L40 | status 对账 rerank_config |
| L42–L44 | chat + health version `v0.32.0` |

---

## rerank_demo.py 全文

```python
"""
Rerank 演示 — 对比关闭 / 开启精排

运行：PYTHONPATH=src python3 src/day32/rerank_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day32.constants import RERANK_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rerank_config import RerankConfig
from rag.reranking_retriever import RerankingRetriever
from rag.retriever_stack import find_reranking


def _top_hit(store: KnowledgeStore, query: str, *, enabled: bool) -> str:
    store.set_rerank_config(RerankConfig(enabled=enabled, candidate_pool=20))
    rag = store.as_rag_service()
    retriever = find_reranking(rag.index.retriever)
    hits = retriever.search(query, top_k=1)
    if not hits:
        return "—"
    preview = hits[0].chunk.text[:40].replace("\n", " ")
    label = "rerank" if enabled else "recall"
    return f"[{label}] {hits[0].chunk.source} ({hits[0].score:.2f}) {preview}…"


def main() -> int:
    print("=" * 60)
    print("  Day 32 Rerank 演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_rerank_config()
    print(f"\n  默认 rerank: enabled={cfg.enabled} pool={cfg.candidate_pool}")

    for item in RERANK_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        print(f"    关闭精排 → {_top_hit(store, q, enabled=False)}")
        print(f"    开启精排 → {_top_hit(store, q, enabled=True)}")

    print("\n  ✅ Rerank 演示完成")
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
PYTHONPATH=src python3 src/day32/rerank_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
pytest tests/day32/test_rerank_api.py -v
```
