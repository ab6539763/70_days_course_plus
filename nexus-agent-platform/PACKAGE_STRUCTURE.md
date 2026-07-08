# NexusAgent 包结构说明

**版本**：v0.35.0（Day 35 多查询扩展）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-035

## Day 35 新增

```
src/rag/query_expander.py
  TemplateQueryExpander / HyDEMockExpander — 单问句 → 多 query
src/rag/expanding_retriever.py
  ExpandingRetriever — 多路 search + merge
src/rag/expansion_config.py
  ExpansionConfig — enabled / mode / max_queries
src/rag/result_merger.py
  merge_retrieval_results — chunk_id 去重
src/day35/
  expansion_demo.py
  expansion_api_demo.py
  phase3_expansion_review.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/expansion-config` | 多 query 扩展开关与参数 |
| PUT | `/api/knowledge/expansion-config` | 更新扩展策略 |
| POST | `/api/knowledge/expansion-preview` | 单条 query 扩展预览 |

`store.json` 新增 `expansion_config` 字段；默认 `enabled=true`，`max_queries=4`。

`POST /api/chat` 响应扩展 `expansion` 审计元数据（queries 列表）。

检索管线（外→内）：`ExpandingRetriever` → `RewritingRetriever` → `RerankingRetriever` → `HybridRetriever`。

## Day 34 新增

```
src/rag/citation_builder.py
  Citation / CitationBundle — 检索结果 → 结构化引用
src/rag/citation_config.py
  CitationConfig — enabled / max_citations / preview_max_chars
src/day34/
  citation_demo.py
  citation_api_demo.py
  phase3_citation_review.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/citation-config` | 引用溯源开关与展示参数 |
| PUT | `/api/knowledge/citation-config` | 更新引用策略 |
| POST | `/api/knowledge/citation-preview` | 单条 query 引用预览 |

`store.json` 新增 `citation_config` 字段；默认 `enabled=true`，`max_citations=3`。

`POST /api/chat` 响应扩展 `citations[]` 与 `rewrite` 审计元数据。

检索管线：`RewritingRetriever` → `RerankingRetriever` → `HybridRetriever`；引用在检索后由 `CitationBuilder` 格式化。

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
