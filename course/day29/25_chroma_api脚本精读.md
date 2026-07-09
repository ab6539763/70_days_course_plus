# Day 29 精读：chroma_api_demo.py 与 API 测试

## chroma_api_demo.py 全文

```python
"""
Chroma API 演示

运行：PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day29/chroma_api_demo.py
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

    print("=== Day 29 Chroma API Demo ===\n")
    status = client.get("/api/knowledge/status").json()
    print(f"  vector_backend: {status.get('vector_backend')}")
    print(f"  chroma_count: {status.get('chroma_count')}")
    print(f"  chunk_count: {status.get('chunk_count')}")

    resp = client.post("/api/knowledge/rebuild", json={"include_sample_docs": True})
    print(f"\n  POST rebuild: {resp.status_code}")
    data = resp.json()
    print(f"    chunks: {data.get('chunks_after')}")

    chat = client.post("/api/chat", json={"message": "产品年化收益？"})
    print(f"\n  POST chat: {chat.status_code}")
    print(f"  version: {client.get('/api/health').json().get('version')}")
    print("\n  ✅ API 演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## 脚本逻辑

1. `set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())` — 注入全局单例  
2. `TestClient(create_app())` — 无需起 uvicorn  
3. 打印 status 的 `vector_backend` / `chroma_count`  
4. `POST /api/knowledge/rebuild` 验证重建后块数  
5. `POST /api/chat` 验证检索链路  
6. `GET /api/health` 读版本号  

## test_chroma_api.py 全文

```python
"""Day 29 Chroma API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.knowledge_store import KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.39.0"


def test_status_includes_chroma_fields(client):
    data = client.get("/api/knowledge/status").json()
    assert data["platform_version"] == "0.39.0"
    assert data["vector_backend"] == "chroma"
    assert data["chroma_count"] == data["chunk_count"]
    assert data["chroma_path"]


def test_rebuild_keeps_chroma_in_sync(client):
    before = client.get("/api/knowledge/status").json()["chroma_count"]
    resp = client.post("/api/knowledge/rebuild", json={"include_sample_docs": True})
    assert resp.status_code == 200
    after = client.get("/api/knowledge/status").json()
    assert after["chroma_count"] == after["chunk_count"]
    assert after["chroma_count"] == resp.json()["chunks_after"]


def test_chat_after_chroma_index(client):
    resp = client.post("/api/chat", json={"message": "产品收益怎么样？"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert body["session_id"]


def test_upload_updates_chroma_count(client, tmp_path):
    md = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not md.is_file():
        pytest.skip("sample md missing")
    with md.open("rb") as fh:
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    assert resp.status_code == 200
    status = client.get("/api/knowledge/status").json()
    assert status["chroma_count"] == status["chunk_count"]
```


## 断言设计点评

- `test_health_version`：平台版本与发版一致  
- `test_status_includes_chroma_fields`：`chroma_count == chunk_count`  
- `test_rebuild_keeps_chroma_in_sync`：rebuild 后仍相等  
- `test_chat_after_chroma_index`：端到端  
- `test_upload_updates_chroma_count`：Day 29 upload 仍全量，但 chroma 同步  

## curl 等价命令

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status
curl -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' -d '{"include_sample_docs": true}'
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' -d '{"message": "产品收益？"}'
```

---

## incremental_api 对比说明（Day 30 预习）

Day 29 的 `test_upload_updates_chroma_count` 验证 upload 后 chroma 仍同步，但**不**验证 reset 未调用——那是 Day 30 `test_incremental_api` 的职责。阅读本测试时注意：Day 29 upload 仍会触发全量 `_rebuild_index`。

---

## Mock 与 TestClient 模式

`chroma_api_demo` 与测试均用 `TestClient` 而非真实 uvicorn，原因：

1. 启动快，适合 CI  
2. 同步调用，不断言端口  
3. `set_knowledge_store` 注入隔离数据  

生产环境行为一致，除非 middleware 依赖真实 ASGI 生命周期。

---

## 字段断言清单（教师）

| 测试 | 关键断言 |
|------|----------|
| test_health_version | version == 平台发版号 |
| test_status_includes_chroma_fields | chroma_count == chunk_count |
| test_rebuild_keeps_chroma_in_sync | rebuild 后仍相等 |
| test_chat_after_chroma_index | reply 非空 |
| test_upload_updates_chroma_count | upload 后仍相等 |
