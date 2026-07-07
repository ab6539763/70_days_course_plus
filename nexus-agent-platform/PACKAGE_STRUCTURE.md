# NexusAgent 包结构说明

**版本**：v0.29.0（Day 29 Chroma 向量库）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-029

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

`store.json` version 升至 **1.1**，新增 `vector_backend: chroma`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/status` | 新增 vector_backend、chroma_path、chroma_count |

rebuild / upload 流程不变，`_rebuild_index` 内部写入 Chroma。

## Day 28 新增

```
src/rag/knowledge_rebuild.py
  collect_source_files()   # sample_docs + uploads
  rebuild_store()          # 全量清空再分块
  rebuild_with_best_config()
src/day28/
  rebuild_demo.py
  rebuild_api_demo.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/rebuild` | 全量重建，可选 apply_best_config |

`store.json` 新增 `last_rebuilt_at` 字段。

## 重建源

1. `data/knowledge/uploads/` — 用户上传  
2. `day02/sample_docs/` — 内置样例（可 include_sample_docs=false 跳过）  

同名文件 uploads 优先。
