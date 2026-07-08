# NexusAgent 包结构说明

**版本**：v0.31.0（Day 31 混合检索）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-031

## Day 31 新增

```
src/rag/hybrid_retriever.py
  HybridRetriever — 关键词 + 向量融合
src/rag/retrieval_config.py
  RetrievalConfig — mode / fusion / 权重
src/day31/
  hybrid_demo.py
  hybrid_api_demo.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/retrieval-config` | 检索模式与融合参数 |
| PUT | `/api/knowledge/retrieval-config` | 更新 vector/keyword/hybrid |

`store.json` 新增 `retrieval_config` 字段；默认 `mode=hybrid`。

## Day 30 新增

```
_incremental_index — upload 增量 upsert
_remove_document_by_source — 同名替换
```

## Day 29 新增

Chroma 双存储：`chroma_store.py` / `chroma_retriever.py`

## Day 28 新增

`knowledge_rebuild.py` — 全量 rebuild

同名文件 uploads 优先。
