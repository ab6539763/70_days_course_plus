# incremental_api 脚本精读

```python
"""
增量索引 API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
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
    store = KnowledgeStore.bootstrap_from_sample_docs()
    set_knowledge_store(store)
    client = TestClient(create_app())

    print("=== Day 30 Incremental API Demo ===\n")
    sample = _SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        print("  sample md missing")
        return 1

    before = client.get("/api/knowledge/status").json()
    print(f"  before: {before['chunk_count']} chunks, mode={before.get('index_mode')}")

    with sample.open("rb") as fh:
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    print(f"  upload: {resp.status_code} index_mode={resp.json().get('index_mode')}")

    with sample.open("rb") as fh:
        resp2 = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    after = client.get("/api/knowledge/status").json()
    print(f"  re-upload docs={after['document_count']} chroma={after['chroma_count']}")
    print(f"  last_incremental_at: {after.get('last_incremental_at')}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## test_incremental_api.py

见 22 精读第十八节 API 测试全文；本节仅摘要：

- `test_upload_returns_incremental_mode` — patch reset==0  
- `test_status_shows_incremental_fields` — last_incremental_at  
- `test_reupload_same_file_no_duplicate_docs` — document_count  
- `test_rebuild_switches_to_full_mode` — rebuild 后 full  
- `test_chat_works_after_incremental_upload` — E2E  

## 关键断言

`test_upload_returns_incremental_mode`：patch reset 为 0，响应含 incremental。

---

## curl 示例

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/upload \
  -F "file=@src/day26/sample_docs/product_notice.md;filename=notice.md"
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '{index_mode,last_incremental_at,chroma_count}'
```

---

## 响应字段说明

| 字段 | 含义 |
|------|------|
| index_mode | incremental / full |
| message | 含「增量」提示文案 |
| chunk_count | 当前总块数 |

---

## 与 Day29 chroma_api 差异

Day29 `test_upload_updates_chroma_count` 不测 reset；Day30 `test_upload_returns_incremental_mode` **必须** mock reset==0。

---

## incremental_api_demo 逐行注释

| 行 | 作用 |
|----|------|
| bootstrap store | 测试数据 |
| before status | 基线 chunk_count |
| 第一次 upload | 建立 incremental 状态 |
| patch reset 内第二次 upload | 核心断言 |
| after status | doc 数、chroma_count |
| health version | 0.30.0 |

---

## 与 upload 路由源码提示

阅读 `api/knowledge.py` 中 `upload` 处理函数，确认 `incremental=True` 传参位置（行号随版本变化，以仓库为准）。
