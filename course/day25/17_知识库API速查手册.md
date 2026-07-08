# 知识库 API 速查手册

**需求**：ZL-NA-REQ-025 | **版本**：0.25.0

## 环境

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

## curl

```bash
# 状态
curl -s http://127.0.0.1:8000/api/knowledge/status | jq

# 上传
curl -s -X POST http://127.0.0.1:8000/api/knowledge/upload \
  -F "file=@custom_faq.txt;type=text/plain"
```

## TestClient

```python
from fastapi.testclient import TestClient
from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store

store = KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp_path / "s.json")
set_knowledge_store(store)
client = TestClient(create_app())
client.get("/api/knowledge/status")
```

## Python 直接入库

```python
from rag.knowledge_store import get_knowledge_store
kb = get_knowledge_store()
kb.ingest_text("内容", filename="a.txt")
kb.save()
```

## 响应字段

| 字段 | 含义 |
|------|------|
| chunk_count | 本次文档块数 |
| total_chunks | 库内总块数 |
| sessions_cleared | 清除会话数 |
| document_count | 文档篇数 |

速查完。


---

## 附录：完整测试夹具（速查专节）

```python
"""Day 25 知识库存储与 ingestion 测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.paths import get_path
from day25.constants import SAMPLE_UPLOAD_TEXT
from rag.embedding import TfidfEmbeddingModel
from rag.ingestion import ingest_upload
from rag.knowledge_store import KnowledgeStore, get_knowledge_store, set_knowledge_store


@pytest.fixture
def tmp_store(tmp_path):
    store_path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=store_path)
    set_knowledge_store(store)
    yield store
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())


def test_bootstrap_
```


速查附录完。

---

## 附录：schemas 字段（速查 vol2）

KnowledgeUploadResponse 见 `api/schemas.py`：`filename`, `format`, `chunk_count`, `document_count`, `total_chunks`, `sessions_cleared`, `index_mode`, `message`。

前端 `renderStatus` 拼接：`document_count 篇 / chunk_count 块`。

速查 vol2 完。

---

## httpie 替代

```bash
http -f POST :8000/api/knowledge/upload file@faq.txt
```
httpie 完。
