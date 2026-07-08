# NexusAgent 包结构说明

**版本**：v0.32.0（Day 32 Rerank 重排序）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-032

## Day 32 新增

```
src/rag/reranker.py
  MockCrossEncoderReranker — query-chunk 逐对打分
src/rag/reranking_retriever.py
  RerankingRetriever — hybrid 召回 + rerank 精排
src/rag/rerank_config.py
  RerankConfig — enabled / candidate_pool / model
src/day32/
  rerank_demo.py
  rerank_api_demo.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/rerank-config` | rerank 开关与候选池 |
| PUT | `/api/knowledge/rerank-config` | 更新精排策略 |

`store.json` 新增 `rerank_config` 字段；默认 `enabled=true`，`candidate_pool=20`。

检索管线：`HybridRetriever` 宽召回 → `MockCrossEncoderReranker` 精排 → top-k。

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
