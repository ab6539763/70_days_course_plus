# Day 38 API 脚本精读

## API demo 全文

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
| 开头 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| TestClient | 创建 app 与测试客户端 |
| bootstrap | 保证语料/知识库已初始化 |
| GET 配置 | 读默认配置 |
| PUT 配置 | 更新配置 — **API 核心演示** |
| status | 对账 config 是否写回 store |
| chat + health | 端到端 + 版本号 `v0.38.0` |

---

## CLI demo 全文

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


---

## constants.py（case studies，query）

```python
RETRY_CASES = (
    ("年化收益怎么样（首次窄召回未命中）",),
    ("彻底答非所问的场景",),
    ("retry_on_fail=false",),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day38/retry_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day38/retry_api_demo.py
pytest tests/day38/ -v
```
