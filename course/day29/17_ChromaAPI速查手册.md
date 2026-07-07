# Chroma API 速查手册（Day 29）

## ChromaVectorIndex

| 方法 | 签名 | 说明 |
|------|------|------|
| `__init__` | `(persist_path, *, collection_name="nexus_knowledge")` | 延迟连接 |
| `reset` | `() -> None` | 删 collection 并重建 |
| `count` | `() -> int` | 当前向量数 |
| `upsert_chunks` | `(chunks, vectors) -> int` | 批量写入 |
| `query` | `(query_vector, *, top_k=3, min_score=0.05)` | 检索 |
| `delete_by_ids` | `(ids: list[str]) -> int` | 按 id 删 |
| `delete_by_source` | `(source: str) -> int` | 按 metadata 删 |

## ChromaEmbeddingRetriever

| 方法 | 说明 |
|------|------|
| `search(query, *, top_k=3)` | 返回 `list[RetrievalResult]` |
| `chunk_count` | 属性，等同 chroma.count() |

## KnowledgeStore（Day 29 相关）

| 方法 | 说明 |
|------|------|
| `_rebuild_index()` | 全量：fit TF-IDF → reset → upsert |
| `_sync_chroma_from_json()` | chroma 空时回填 |
| `_chroma_index()` | 工厂，解析 chroma_path |
| `status_dict()` | 含 chroma 字段 |

## HTTP

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '{vector_backend,chroma_count,chunk_count}'
```

## 环境变量

| 变量 | 用途 |
|------|------|
| PYTHONPATH=src | 导入路径 |
| NEXUS_LLM_MOCK=1 | 测试 mock LLM |

## 常量

- `VECTOR_BACKEND = "chroma"`  
- `COLLECTION_NAME = "nexus_knowledge"`  
- `STORE_VERSION = "1.1"`  

---

## Python 交互示例

```python
from pathlib import Path
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

store = KnowledgeStore.load_or_bootstrap()
idx = store._chroma_index()
print(idx.count(), store.chunk_count)
```

---

## 错误码与异常（教学）

| 异常 | 场景 |
|------|------|
| ValueError chunks/vectors 不一致 | upsert 参数错误 |
| chromadb 未安装 | import 失败 |
| sqlite locked | 多进程写同 path |

---

## REST 响应示例（status 节选）

```json
{
  "platform_version": "0.30.0",
  "document_count": 3,
  "chunk_count": 12,
  "vector_backend": "chroma",
  "chroma_path": "/app/data/knowledge/chroma",
  "chroma_count": 12,
  "chunk_config": { "chunk_size": 200, "overlap": 40, "strategy": "auto", "name": "default" },
  "last_rebuilt_at": "2026-08-04T10:00:00Z",
  "index_mode": "full"
}
```

注：`index_mode` / `last_incremental_at` 字段在 Day 30 增量路径更常用；Day 29 rebuild 后一般为 `full`。

---

## CLI 速查

```bash
# 只看 chroma 字段
curl -s localhost:8000/api/knowledge/status | python3 -m json.tool | grep chroma

# 健康
curl -s localhost:8000/api/health | jq .version
```
