# Day 37 API 脚本精读

## API demo 全文

```python
"""
Validation API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/validation_api_demo.py
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

    print("=== Day 37 Validation API Demo ===\n")
    cfg = client.get("/api/knowledge/validation-config").json()
    print(f"  enabled={cfg.get('enabled')} min_score={cfg.get('min_score')}")

    preview = client.post(
        "/api/knowledge/validation-preview",
        json={
            "query": "年化收益怎么样",
            "reply": "今天北京天气晴朗，适合出游。",
        },
    )
    print(f"  validation-preview: {preview.status_code}")
    body = preview.json()
    print(f"  passed={body.get('passed')} score={body.get('score')}")

    chat = client.post("/api/chat", json={"message": "客服电话多少？"})
    print(f"  chat: {chat.status_code}")
    chat_body = chat.json()
    if chat_body.get("validation"):
        print(f"  validation passed={chat_body['validation'].get('passed')}")
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
| chat + health | 端到端 + 版本号 `v0.37.0` |

---

## CLI demo 全文

```python
"""
Self-RAG 答案校验演示 — reply vs citations 一致性

运行：PYTHONPATH=src python3 src/day37/validation_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from day37.constants import VALIDATION_CASES
from rag.answer_validator import RuleBasedAnswerValidator
from rag.knowledge_store import KnowledgeStore
from rag.validation_config import ValidationConfig


def main() -> int:
    print("=" * 60)
    print("  Day 37 Self-RAG 答案校验演示")
    print("=" * 60)

    store = KnowledgeStore.bootstrap_from_sample_docs()
    cfg = store.get_validation_config()
    validator = RuleBasedAnswerValidator(config=cfg)
    print(f"\n  validation enabled={cfg.enabled} min_score={cfg.min_score}")

    for item in VALIDATION_CASES:
        q = item["query"]
        reply = item["reply"]
        cite_data = store.fetch_citations(q)
        citations = cite_data.get("citations") or []
        result = validator.validate(q, reply, citations)
        flag = "✅" if result.passed == item["expect_passed"] else "⚠️"
        print(f"\n  Q: {q}")
        print(f"    passed={result.passed} score={result.score:.2f} {flag}")
        print(f"    reason: {result.reason}")
        if citations:
            print(f"    citations: {len(citations)} matched={list(result.matched_citation_ranks)}")

    print("\n  ✅ Validation 演示完成")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

## constants.py（case studies，query）

```python
VALIDATION_CASES = (
    ("客服电话多少 → 客服热线是 400-888-1234",),
    ("年化收益怎么样 → 今天北京天气晴朗",),
    ("min_score 附近的部分匹配回答",),
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day37/validation_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/validation_api_demo.py
pytest tests/day37/ -v
```
