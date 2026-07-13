# Day 36 课件索引

**主题**：自适应路由（Query Router） — route → expand? → rewrite → hybrid → rerank → citations
**需求**：ZL-NA-REQ-036
**平台版本**：v0.36.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `rag/query_router.py` | RuleBasedQueryRouter — faq_fast / rag_standard / rag_wide |
| `rag/routing_retriever.py` | RoutingRetriever — 动态 expand/rewrite 开关 |
| `rag/route_config.py` | RouteConfig — enabled / fallback_intent |

| API | 说明 |
|-----|------|
| GET/PUT /api/knowledge/route-config | 配置读写 |
| POST /api/knowledge/route-preview | 无状态预览 |

`POST /api/chat` 响应体在管线经过本日模块处理后附带相应审计字段。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day36/route_demo.py
python3 src/day36/route_api_demo.py
python3 -m pytest tests/day36/ -v
```

## 关键流程

Day 35 让检索更广；Day 36 让管线更省 — 按问句意图动态决定是否要 expand/rewrite。

## 验收

`tests/day36/` 20 项全绿。

---

## 课件生成

```bash
python3 scripts/generate_day36_course.py
```
