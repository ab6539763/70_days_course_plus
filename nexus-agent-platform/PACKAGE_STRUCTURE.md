# NexusAgent 包结构说明

**版本**：v0.38.0（Day 38 多轮 Self-RAG 校验重试）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-038

## Day 38 新增

```
src/rag/validation_retry.py
  apply_validation_retry — 校验失败后 rag_wide 重检索再校验
src/rag/knowledge_store.py
  fetch_citations_retry — 放大 pool + intent_override
src/day38/
  retry_demo.py
  retry_api_demo.py
  phase3_retry_review.py
```

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/validation-retry-preview` | 模拟 retry 宽召回后再校验 |

`POST /api/chat` 在 `retry_on_fail=true` 时执行重试循环；`validation` 含 `retries`、`retry_route`。

## Day 37 新增

```
src/rag/answer_validator.py
  RuleBasedAnswerValidator — 引用-回复一致性打分
src/rag/validation_config.py
  ValidationConfig — enabled / min_score / refuse_on_fail
src/day37/
  validation_demo.py
  validation_api_demo.py
  phase3_validation_review.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/validation-config` | 答案校验开关与阈值 |
| PUT | `/api/knowledge/validation-config` | 更新校验策略 |
| POST | `/api/knowledge/validation-preview` | 单条 query+reply 校验预览 |

`store.json` 新增 `validation_config` 字段；默认 `enabled=true`，`min_score=0.35`。

`POST /api/chat` 响应扩展 `validation` 审计元数据（passed、score、reason）。

管线：`route → expand? → rewrite → hybrid → rerank → citations → LLM → validate`

## Day 36 新增

```
src/rag/query_router.py
  RuleBasedQueryRouter — faq_fast / rag_standard / rag_wide
src/rag/routing_retriever.py
  RoutingRetriever — 动态 expand/rewrite 开关
src/rag/route_config.py
  RouteConfig — enabled / fallback_intent
src/day36/
  route_demo.py
  route_api_demo.py
  phase3_route_review.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/route-config` | 路由开关与默认意图 |
| PUT | `/api/knowledge/route-config` | 更新路由策略 |
| POST | `/api/knowledge/route-preview` | 单条 query 路由预览 |

`store.json` 新增 `route_config` 字段；默认 `enabled=true`，`fallback_intent=rag_standard`。

`POST /api/chat` 响应扩展 `route` 审计元数据（intent、expand、rewrite）。

检索管线（外→内）：`RoutingRetriever` → `ExpandingRetriever` → `RewritingRetriever` → …

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
