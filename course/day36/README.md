# Day 36 课件索引

**日期**：2026-08-12（星期一）  
**主题**：自适应路由（Query Router）— route → expand? → rewrite → hybrid → rerank → citations  
**需求**：ZL-NA-REQ-036  
**平台版本**：v0.36.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| QueryRouter | `rag/query_router.py` | faq_fast / rag_standard / rag_wide |
| RoutingRetriever | `rag/routing_retriever.py` | 动态 expand/rewrite 开关 |
| RouteConfig | `rag/route_config.py` | enabled、fallback_intent |
| route API | `api/knowledge.py` | GET/PUT route-config + route-preview |
| chat route | `api/chat.py` | reply + route + citations + rewrite + expansion |
| 演示 | `day36/route_demo.py` | 意图路由对比 |
| 测试 | `tests/day36/` | 20 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day36/route_demo.py
python3 src/day36/route_api_demo.py
python3 -m pytest tests/day36/ -v
```

## 关键流程

Day 35 让检索**更广** → Day 36 让管线**更省**：`RuleBasedQueryRouter` 对「客服电话」走 faq_fast（跳过 expand/rewrite），对「理财安全吗」走 rag_wide（全管线）。

## 核心难点（必读）

**路由 vs 扩展**：Day35 默认全量 expand；Day36 按意图动态开关 expand/rewrite，平衡延迟与 Recall。

## 设计决策

1. `RouteConfig` 默认 `enabled=True`, `fallback_intent=rag_standard`  
2. `faq_fast`：电话类 query 跳过 expand + rewrite  
3. `rag_wide`：安全/合规类 query 开启 expand + rewrite  
4. 前端 `msg__route` 展示 intent 与开关状态  

## 验收

通过标准：`test_route_preview` 返回 faq_fast；`test_chat_includes_route` 绿。

---

## 四阶段 RAG 全景

| 阶段 | 组件 | 输出 |
|------|------|------|
| 路由 | RoutingRetriever | intent + expand/rewrite |
| 扩展 | ExpandingRetriever | queries[] |
| 改写 | RewritingRetriever | rewritten query |
| 召回+融合 | HybridRetriever | candidates |
| 精排 | RerankingRetriever | top-k |
| 溯源 | CitationBuilder | citations[] |

---

## 课件生成

```bash
python3 scripts/course_days/day36.py
```

## 版本历史

| 版本 | 说明 |
|------|------|
| v0.36.0 | route-config + RoutingRetriever + 前端 route 展示 |
