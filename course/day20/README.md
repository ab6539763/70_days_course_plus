# Day 20 课件索引

**日期**：2026-07-25（星期六）  
**主题**：Embedding 与向量相似度检索  
**需求**：ZL-NA-REQ-020  
**里程碑**：Phase 2 / Sprint 3 第六日（Day 15–24）

## Sprint 3 进度

昨日完成关键词 RAG，今日将 `KeywordRetriever` 升级为 **EmbeddingRetriever**：TF-IDF 向量化 + 余弦相似度，并落地 FAQ 相似问题匹配。

- Day 15 Token 计数 → Day 16 流式输出 → Day 17 Prompt 模板 → Day 18 意图分类 → Day 19 RAG 关键词检索 → **Day 20 Embedding 向量检索**
- Day 21 Sprint 3 周测 / 工具调用整合……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 余弦相似度与 TF-IDF Embedding 演示
python3 src/day20/embedding_demos.py

# 关键词 vs 向量检索对比
python3 src/day20/vector_search_demos.py

# FAQ 相似问题匹配
python3 src/day20/faq_matcher_demo.py

# Embedding RAG + 意图路由 + /similar 联调
NEXUS_LLM_MOCK=1 python3 src/day20/routed_embedding_demo.py

# 单元测试（12 项）
python3 -m pytest tests/day20/test_embedding.py -v
```

## 今日交付物

- [x] `src/rag/vector.py` — `cosine_similarity`、`dot_product`、`vector_norm`
- [x] `src/rag/embedding.py` — `TfidfEmbeddingModel`、`EmbeddingClient`、`EmbeddingVector`
- [x] `src/rag/synonyms.py` — `TOKEN_SYNONYMS`、`PHRASE_GROUPS`、`expand_tokens`
- [x] `src/rag/embedding_retriever.py` — `EmbeddingRetriever`、`IndexedChunk`
- [x] `src/rag/context.py` — `use_embedding=True` 工厂参数
- [x] `services/faq_matcher.py` — `SimilarQuestionMatcher`、`FaqEntry`
- [x] `chat/cli_assistant.py` — `/similar` 命令、`faq_matcher`
- [x] `src/day20/embedding_demos.py`、`vector_search_demos.py`、`faq_matcher_demo.py`、`routed_embedding_demo.py`
- [x] `tests/day20/test_embedding.py`（12 tests）
- [x] Day 20 全套课件（28 篇 + 本 README）

## 上下文链

```
Day 19 KeywordRetriever 字面重叠 → Day 20 EmbeddingRetriever 余弦相似度
Day 19 /retrieve 预览检索 → Day 20 /similar 预览 FAQ 匹配
Day 19 query_context_provider → Day 20 use_embedding=True 提升同义词召回
Day 20 TF-IDF MVP → Day 25+ 密集向量 API 与向量库
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | Embedding 向量检索详解 | 深度专题 |
| 12-14 | 练习册 / 密集向量扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day19 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | Embedding 讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **接口不变**：`EmbeddingRetriever.search` 与 `KeywordRetriever` 同签名，可注入 `DocumentIndex`
2. **TF-IDF MVP**：`TfidfEmbeddingModel` 完全离线，CI 秒级，教学演示余弦相似度原理
3. **同义词扩展**：`synonyms.py` 弥补 TF-IDF 稀疏性，演示「投资回报率」→「年化收益」召回
4. **双预览命令**：`/retrieve` 看文档片段，`/similar` 看 FAQ 匹配，调试互不干扰
5. **门面模式**：`EmbeddingClient` 封装模型，Day 25+ 可替换 HTTP Embedding API

## Day 21 预告

明日 **Sprint 3 周测**：多轮对话 + 工具调用整合，回顾 Day 15–20 全链路能力，为 FastAPI 网页版 Chat 铺路。
