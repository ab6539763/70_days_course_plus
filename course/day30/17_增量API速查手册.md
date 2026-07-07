# 增量 API 速查

## ingest

```python
store.ingest_bytes(data, filename="x.md", incremental=True)
store.ingest_parsed(parsed, incremental=False)  # 默认
```

## status 字段

- `index_mode`  
- `last_incremental_at`  
- `chroma_count`  

## 常量

- `INDEX_MODE_INCREMENTAL = "incremental"`  
- `INDEX_MODE_FULL = "full"`  

---

## upload 响应示例

```json
{
  "message": "文档已增量索引",
  "filename": "notice.md",
  "format": "md",
  "chunk_count": 18,
  "index_mode": "incremental"
}
```

---

## status 完整示例

```json
{
  "platform_version": "0.30.0",
  "document_count": 4,
  "chunk_count": 18,
  "chroma_count": 18,
  "index_mode": "incremental",
  "last_incremental_at": "2026-08-06T09:15:00Z",
  "last_rebuilt_at": "2026-08-05T16:00:00Z",
  "vector_backend": "chroma"
}
```

---

## Python 速查

```python
from rag.knowledge_store import INDEX_MODE_INCREMENTAL
store.ingest_bytes(b"...", filename="a.md", incremental=True)
assert store.index_mode == INDEX_MODE_INCREMENTAL
```
