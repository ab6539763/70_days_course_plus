# hybrid_api 脚本精读

## hybrid_api_demo.py 全文

```python
"""
混合检索 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
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

    print("=== Day 31 Hybrid API Demo ===\n")
    cfg = client.get("/api/knowledge/retrieval-config").json()
    print(f"  mode={cfg.get('mode')} fusion={cfg.get('fusion')}")

    resp = client.put(
        "/api/knowledge/retrieval-config",
        json={"mode": "hybrid", "fusion": "rrf", "keyword_weight": 0.4, "vector_weight": 0.6},
    )
    print(f"  PUT retrieval-config: {resp.status_code}")

    status = client.get("/api/knowledge/status").json()
    print(f"  retrieval mode: {status.get('retrieval_config', {}).get('mode')}")

    chat = client.post("/api/chat", json={"message": "最低起购金额？"})
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
| L21–L22 | 导入 TestClient 与 app 工厂 |
| L26 | `bootstrap_from_sample_docs` 保证可检索语料 |
| L27 | `set_knowledge_store` 测试注入单例 |
| L30–L31 | GET 默认 hybrid 配置 |
| L33–L37 | PUT 切 `fusion=rrf` — **API 核心演示** |
| L39–L40 | status 对账 retrieval_config |
| L42–L43 | chat 端到端 |
| L44 | health version `v0.31.0` |

---

## hybrid_demo.py 全文

```python
"""
混合检索演示 — 对比 vector / keyword / hybrid

运行：PYTHONPATH=src python3 src/day31/hybrid_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day31.constants import HYBRID_QUERIES
from rag.hybrid_retriever import HybridRetriever
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import (
    MODE_HYBRID,
    MODE_KEYWORD,
    MODE_VECTOR,
    RetrievalConfig,
)


def _top_source(store: KnowledgeStore, query: str, mode: str) -> str:
    cfg = RetrievalConfig(mode=mode)
    store.set_retrieval_config(cfg)
    rag = store.as_rag_service()
    retriever = rag.index.retriever
    if not isinstance(retriever, HybridRetriever):
        raise RuntimeError("expected HybridRetriever")
    hits = retriever.search(query, top_k=1)
    if not hits:
        return "—"
    preview = hits[0].chunk.text[:40].replace("\n", " ")
    return f"{hits[0].chunk.source} ({hits[0].score:.2f}) {preview}…"


def main() -> int:
    print("=" * 60)
    print("  Day 31 混合检索演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID))
    print(f"\n  默认模式: {store.get_retrieval_config().mode}")
    print(f"  融合: {store.get_retrieval_config().fusion}")

    for item in HYBRID_QUERIES:
        q = item["query"]
        print(f"\n  Q: {q}")
        for mode in (MODE_VECTOR, MODE_KEYWORD, MODE_HYBRID):
            print(f"    {mode:8s} → {_top_source(store, q, mode)}")

    print("\n  ✅ 混合检索演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


`_top_source` 每次改 mode 后 `as_rag_service()` — 注意性能；教学可接受。

---

## constants.py

```python
HYBRID_QUERIES = (
    {"query": "年化收益率可达", "expect_any": ("8%", "年化")},
    {"query": "13900001111", "expect_any": ("13900001111", "联系")},
    {"query": "投资有风险", "expect_any": ("风险", "谨慎")},
)
```

三条覆盖语义 / 精确 / 合规关键词。

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day31/hybrid_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
pytest tests/day31/test_hybrid_api.py -v
```
