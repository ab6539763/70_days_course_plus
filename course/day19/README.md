# Day 19 课件索引

**日期**：2026-07-24（星期五）  
**主题**：RAG 检索入门 — 查询感知上下文管线  
**需求**：ZL-NA-REQ-019  
**里程碑**：Phase 2 / Sprint 3 第五日（Day 15–24）

## Sprint 3 进度

昨日完成意图路由，今日将 `context_provider` 从静态 `doc_reader` 截断升级为**查询感知 RAG 检索管线**：

- Day 15 Token 计数 → Day 16 流式输出 → Day 17 Prompt 模板 → Day 18 意图分类 → **Day 19 RAG 检索**
- Day 20 Embedding / 向量相似度检索……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 文档分块演示
python3 src/day19/chunk_demos.py

# 关键词检索演示
python3 src/day19/retriever_demos.py

# RAG 上下文拼接演示
python3 src/day19/rag_context_demo.py

# RAG + 意图路由 + ChatAssistant 联调
NEXUS_LLM_MOCK=1 python3 src/day19/routed_rag_demo.py

# 单元测试（12 项）
python3 -m pytest tests/day19/test_rag.py -v
```

## 今日交付物

- [x] `src/rag/chunker.py` — `TextChunk`、`chunk_text`、`chunk_documents`
- [x] `src/rag/retriever.py` — `KeywordRetriever`、`RetrievalResult`
- [x] `src/rag/context.py` — `RAGContextService`、`DocumentIndex`
- [x] `prompts/intent.py` — `query_context_provider` 查询感知上下文
- [x] `chat/cli_assistant.py` — `/retrieve` 命令、`rag_service`
- [x] `src/day19/chunk_demos.py`、`retriever_demos.py`、`rag_context_demo.py`、`routed_rag_demo.py`
- [x] `tests/day19/test_rag.py`（12 tests）
- [x] Day 19 全套课件（28 篇 + 本 README）

## 上下文链

```
Day 18 context_provider 静态截断 → Day 19 query_context_provider 检索管线
Day 18 IntentRouter.build_variables → Day 19 rag_qa 注入真实检索片段
Day 18 /route 预览意图 → Day 19 /retrieve 预览检索命中
Day 19 关键词检索 MVP → Day 20 Embedding 向量相似度
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | RAG 检索详解 | 深度专题 |
| 12-14 | 练习册 / Embedding 扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day18 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | RAG 讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **分块优先**：段落合并 + 滑动窗口 + overlap，避免语义在块边界断裂  
2. **关键词 MVP**：`KeywordRetriever` 零向量库依赖，CI 可离线跑通  
3. **查询感知注入**：`query_context_provider(query)` 替代无参 `context_provider()`  
4. **服务层封装**：`RAGContextService` 串联 doc_reader → chunker → retriever → context 字符串  
5. **双预览命令**：`/route` 看意图，`/retrieve` 看检索命中，调试互不干扰  

## Day 20 预告

明日引入 **Embedding 与向量相似度检索**：`KeywordRetriever` 可替换为向量检索器，`context` 质量将显著提升，为 Day 25+ 向量库集成铺路。
