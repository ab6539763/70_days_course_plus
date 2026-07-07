# NexusAgent 包结构说明

**版本**：v0.30.0（Day 30 增量索引）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-030

## Day 30 新增

```
src/rag/knowledge_incremental.py
  IncrementalReport
KnowledgeStore._incremental_index()
KnowledgeStore._remove_document_by_source()
chroma_store.delete_by_ids / delete_by_source
src/day30/
  incremental_demo.py
  incremental_api_demo.py
```

## 双路径索引

| 触发 | 方法 | Chroma |
|------|------|--------|
| POST /upload | `_incremental_index` | upsert only |
| POST /rebuild | `_rebuild_index` | reset + upsert |

`store.json` 新增 `last_incremental_at`、`index_mode`。

## Day 29 新增

```
src/rag/chroma_store.py
  ChromaVectorIndex      # PersistentClient 封装
  upsert_chunks / query / reset
src/rag/chroma_retriever.py
  ChromaEmbeddingRetriever
src/day29/
  chroma_demo.py
  chroma_api_demo.py
```

## 双存储

| 组件 | 路径 | 内容 |
|------|------|------|
| store.json | data/knowledge/ | documents、chunks、TF-IDF 词表 |
| Chroma | data/knowledge/chroma/ | 向量 + chunk metadata |

`store.json` version **1.1**，`vector_backend: chroma`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/status` | vector_backend、index_mode、chroma_count |
| POST | `/api/knowledge/upload` | 增量索引，响应含 index_mode |

## Day 28 新增

```
src/rag/knowledge_rebuild.py
  rebuild_store()          # 全量清空再分块
```

| POST | `/api/knowledge/rebuild` | 全量重建 |

同名文件 uploads 优先。
