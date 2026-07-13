# Day 35 课件索引

**主题**：多查询扩展（Query Expansion / HyDE） — rewrite → hybrid → rerank → expansion.queries + merged citations
**需求**：ZL-NA-REQ-035
**平台版本**：v0.35.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `rag/query_expander.py` | QueryExpander — Template / HyDE mock 扩展 |
| `rag/expanding_retriever.py` | ExpandingRetriever — 多路 search + merge |
| `rag/expansion_config.py` | ExpansionConfig — enabled / max_queries / per_query_top_k |
| `rag/result_merger.py` | merge_retrieval_results — chunk_id 去重合并 |

| API | 说明 |
|-----|------|
| GET/PUT /api/knowledge/expansion-config | 配置读写 |
| POST /api/knowledge/expansion-preview | 无状态预览 |

`POST /api/chat` 响应体在管线经过本日模块处理后附带相应审计字段。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day35/expansion_demo.py
python3 src/day35/expansion_api_demo.py
python3 -m pytest tests/day35/ -v
```

## 关键流程

Day 34 让回答有据可查；Day 35 让检索更广更全 — 一条问句拓展成多条 query 再合并召回。

## 验收

`tests/day35/` 20 项全绿。

---

## 课件生成

```bash
python3 scripts/generate_day35_course.py
```
