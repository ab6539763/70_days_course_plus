# Day 34 课件索引

**日期**：2026-08-10（星期一）  
**主题**：引用溯源（Citation Traceability）— rewrite → hybrid → rerank → citations[]  
**需求**：ZL-NA-REQ-034  
**平台版本**：v0.34.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| CitationBuilder | `rag/citation_builder.py` | Citation / CitationBundle |
| CitationConfig | `rag/citation_config.py` | enabled、max_citations、preview |
| retrieve_citation_bundle | `rag/context.py` | 检索 + 结构化引用 |
| fetch_citations | `rag/knowledge_store.py` | 知识库层封装 |
| citation API | `api/knowledge.py` | GET/PUT + citation-preview |
| chat citations | `api/chat.py` | reply + citations[] + rewrite |
| 演示 | `day34/citation_demo.py` | 引用列表打印 |
| 测试 | `tests/day34/` | 20 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day34/citation_demo.py
python3 src/day34/citation_api_demo.py
python3 -m pytest tests/day34/ -v
```

## 关键流程

Day 33 让用户**问对问题** → Day 34 让回答**有据可查**：`POST /api/chat` 在 `reply` 之外返回 `citations[]`（source、score、preview、chunk_id），并附带 `rewrite` 审计元数据。

## 核心难点（必读）

**引用 vs 生成**：citations 来自检索结果，不是 LLM 编造；`chunk_id` 可追溯到 `store.json` 分块。

## 设计决策

1. `CitationConfig` 默认 `enabled=True`, `max_citations=3`  
2. `include_rewrite_meta=True` 展示改写审计链  
3. `fetch_citations` 在 chat 后与 reply 一并返回  
4. 前端 `msg__citations` 展示引用列表  

## 验收

通过标准：`test_chat_includes_citations` 绿；`citation-preview` 返回 ≥1 条 source。

---

## 四阶段 RAG 全景

| 阶段 | 组件 | 输出 |
|------|------|------|
| 改写 | RewritingRetriever | rewritten query |
| 召回+融合 | HybridRetriever | candidates |
| 精排 | RerankingRetriever | top-k |
| 溯源 | CitationBuilder | citations[] |

---

## 课件生成

```bash
python3 scripts/course_days/day34.py
```

## 版本历史

| 版本 | 说明 |
|------|------|
| v0.34.0 | citation-config + chat citations + 前端展示 |
