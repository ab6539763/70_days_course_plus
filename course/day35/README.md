# Day 35 课件索引

**日期**：2026-08-11（星期一）  
**主题**：多查询扩展（Query Expansion / HyDE）— rewrite → hybrid → rerank → expansion.queries + merged citations  
**需求**：ZL-NA-REQ-035  
**平台版本**：v0.35.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| QueryExpander | `rag/query_expander.py` | Template / HyDE mock 扩展 |
| ExpandingRetriever | `rag/expanding_retriever.py` | 多路 search + merge |
| ExpansionConfig | `rag/expansion_config.py` | enabled、max_queries、per_query_top_k |
| result_merger | `rag/result_merger.py` | chunk_id 去重合并 |
| expansion API | `api/knowledge.py` | GET/PUT expansion-config + expansion-preview |
| chat expansion | `api/chat.py` | reply + expansion + citations + rewrite |
| 演示 | `day35/expansion_demo.py` | 多 query 对比打印 |
| 测试 | `tests/day35/` | 20 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day35/expansion_demo.py
python3 src/day35/expansion_api_demo.py
python3 -m pytest tests/day35/ -v
```

## 关键流程

Day 34 让回答**有据可查** → Day 35 让检索**更广更全**：`ExpandingRetriever` 将「理财安全吗」扩展为多条 query，多路召回后按 `chunk_id` 去重合并，再进入 citations 展示。

## 核心难点（必读）

**扩展 vs 改写**：Day33 rewrite 规范单条 query；Day35 expand 生成多条 query 拓宽召回面。延迟 ≈ `len(queries) × 单路检索`。

## 设计决策

1. `ExpansionConfig` 默认 `enabled=True`, `max_queries=4`  
2. `mode=templates` 规则扩展；`hyde_mock` 追加假设文档 query  
3. `merge_retrieval_results` 按 chunk_id 保留最高分  
4. 前端 `msg__expansion` 展示扩展 query 列表  

## 验收

通过标准：`test_expansion_preview` 返回 ≥2 条 queries；`test_chat_includes_expansion` 绿。

---

## 四阶段 RAG 全景

| 阶段 | 组件 | 输出 |
|------|------|------|
| 扩展 | ExpandingRetriever | queries[] |
| 改写 | RewritingRetriever | rewritten query |
| 召回+融合 | HybridRetriever | candidates |
| 精排 | RerankingRetriever | top-k |
| 溯源 | CitationBuilder | citations[] |

---

## 课件生成

```bash
python3 scripts/course_days/day35.py
```

## 版本历史

| 版本 | 说明 |
|------|------|
| v0.35.0 | expansion-config + ExpandingRetriever + merge + 前端 expansion |
