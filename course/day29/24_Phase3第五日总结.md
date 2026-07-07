# Phase 3 第五日总结（Day 25–29）

## 进度条

| Day | 主题 | 版本 |
|-----|------|------|
| 25 | KnowledgeStore MVP | 0.25.0 |
| 26 | Markdown/PDF 解析 | 0.26.0 |
| 27 | 分块调参 A/B | 0.27.0 |
| 28 | 全量 rebuild | 0.28.0 |
| 29 | Chroma 向量库 | v0.29.0 |

## Day 29 在 Phase 3 的位置

**基础设施层**从「单文件 JSON」升级为「JSON + 向量库双存储」，为 Day 30 增量索引、Day 31 混合检索打地基。

## 关键技能树

```
KnowledgeStore
├── ingest / save / load
├── _rebuild_index  ──→  Chroma reset + upsert
├── _sync_chroma_from_json
└── as_rag_service  ──→  ChromaEmbeddingRetriever
```

## 团队贡献

- 陈默：架构与 PRD  
- 林晓：chroma_store + store 集成  
- 周航：15 项测试 + CI  
- 赵岩：运维备份 SOP  

## 明日 Day 30

upload 增量、同名替换、`index_mode` 字段。请预习 `27_Day30增量索引预习.md`。

---

## Day 25–29 代码行数成长（示意）

| Day | 新增核心文件 | 测试数 |
|-----|-------------|--------|
| 25 | knowledge_store | 12 |
| 26 | doc_parser, chunk_strategies | 17 |
| 27 | chunk_config, retrieval_eval | 15 |
| 28 | knowledge_rebuild | 14 |
| 29 | chroma_store, chroma_retriever | 15 |

Phase 3 知识库栈已具 **存-读-调-发-索引** 闭环。

---

## 知识自检 20 问（Phase 3 综合）

1. KnowledgeStore 权威数据源？  
2. rebuild 与 evaluate 区别？  
3. chunk_config 何时生效？  
4. uploads 与 sample 优先级？  
5. Chroma 存什么不存什么？  
6. ……（教师可口播其余 15 问）

---

## 致谢

感谢产品部提供真实 PDF 样例，运维部提供备份窗口，QA 通宵跑 regression。
