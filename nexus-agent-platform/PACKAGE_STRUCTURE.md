# NexusAgent 包结构说明

**版本**：v0.33.0（Day 33 查询改写）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-033

## Day 33 新增

```
src/rag/query_rewriter.py
  RuleBasedQueryRewriter — 规则表改写口语问句
src/rag/rewriting_retriever.py
  RewritingRetriever — 改写后委托 inner 检索
src/rag/rewrite_config.py
  RewriteConfig — enabled / mode / fallback
src/day33/
  rewrite_demo.py
  rewrite_api_demo.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/rewrite-config` | 改写开关与模式 |
| PUT | `/api/knowledge/rewrite-config` | 更新改写策略 |
| POST | `/api/knowledge/rewrite-preview` | 单条 query 改写预览 |

`store.json` 新增 `rewrite_config` 字段；默认 `enabled=true`，`mode=rules`。

检索管线：`RewritingRetriever` → `RerankingRetriever` → `HybridRetriever`。

## Day 32 新增

```
src/rag/reranker.py
  MockCrossEncoderReranker — query-chunk 逐对打分
src/rag/reranking_retriever.py
  RerankingRetriever — hybrid 召回 + rerank 精排
```

## Day 31 新增

HybridRetriever + retrieval-config API

## Day 30 新增

_incremental_index — upload 增量 upsert

## Day 29 新增

Chroma 双存储

## Day 28 新增

`knowledge_rebuild.py` — 全量 rebuild
