# Day 29 课件索引

**日期**：2026-08-05（星期三）  
**主题**：Chroma 向量库持久化  
**需求**：ZL-NA-REQ-029

## 今日交付

- `rag/chroma_store.py` — ChromaVectorIndex 持久化封装
- `rag/chroma_retriever.py` — ChromaEmbeddingRetriever
- `KnowledgeStore` 向量索引迁移至 Chroma，JSON 保留 TF-IDF 词表
- `GET /api/knowledge/status` 增加 vector_backend / chroma_count
- `tests/day29/` 15 项

```bash
PYTHONPATH=src python3 src/day29/chroma_demo.py
PYTHONPATH=src pytest tests/day29/ -q
```

## 关键流程

Day 28 rebuild 流程不变 → Day 29 **换索引引擎**：向量落盘 `data/knowledge/chroma/`。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day29/chroma_demo.py
python3 src/day29/chroma_api_demo.py
python3 -m pytest tests/day29/ -v
```

## 设计决策

1. **双存储**：store.json 存元数据 + TF-IDF 词表；Chroma 存向量  
2. **重建不变**：`_rebuild_index()` 先 fit TF-IDF 再 upsert Chroma  
3. **冷启动迁移**：load 时若 Chroma 空则从 JSON 自动回填  
4. **评估隔离**：Day 27 A/B 仍用内存 EmbeddingRetriever，避免污染生产 Chroma  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_Chroma向量库详解 | 专题 |
| 22_chroma_store精读 | 源码 |
| 27_Day30预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day29/chroma_api_demo.py
```
