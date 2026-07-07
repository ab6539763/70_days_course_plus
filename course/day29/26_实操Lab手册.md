# Day 29 Lab

**需求**：ZL-NA-REQ-029

## 概述

六步。

## 核心知识点

### 1. 为何引入 Chroma？

Day 25–28 向量与词表挤在 `store.json`，随 chunk 增长文件膨胀、全量 load 变慢。Chroma 提供**专用向量持久化**与 ANN 检索能力（教学规模仍可用线性 scan 等价路径）。

### 2. 双存储架构

| 存储 | 内容 | 路径 |
|------|------|------|
| JSON | documents、chunks、TF-IDF vocab/idf | store.json |
| Chroma | chunk_id、embedding、metadata | data/knowledge/chroma |

### 3. _rebuild_index 新流程

1. EmbeddingRetriever(chunks) 训练 TF-IDF  
2. embedding_state = export_state()  
3. chroma.reset()  
4. chroma.upsert_chunks(chunks, vectors)  

### 4. ChromaVectorIndex API

- `reset()` — 删除 collection  
- `upsert_chunks()` — 写入向量  
- `query()` — 按 query_embedding 检索  
- `count()` — 当前向量数  

### 5. ChromaEmbeddingRetriever

实现与 EmbeddingRetriever 相同的 `search(query, top_k)`，供 DocumentIndex 无感切换。

### 6. 与 Day 28 rebuild 关系

`rebuild_store` 仍调用 `_rebuild_index()`，无需修改 rebuild 模块；换的是索引实现。

### 7. 评估路径隔离

`retrieval_eval.build_retriever_for_doc` 仍用内存 EmbeddingRetriever，避免 A/B 实验写入生产 Chroma。

### 8. status 新字段

```json
{
  "vector_backend": "chroma",
  "chroma_path": "/.../data/knowledge/chroma",
  "chroma_count": 12
}
```

### 9. Day 30 预告

增量索引：单文档 upload 仅 upsert 对应 chunk，无需全量 reset。

### 10. 运维注意

备份需同时包含 store.json 与 chroma 目录；仅删 JSON 会导致元数据丢失。

### 11. 课堂检查清单

- [ ] chroma_count == chunk_count  
- [ ] rebuild 后 Chroma 与 JSON 一致  
- [ ] chat 检索仍返回相关片段  
- [ ] 删除 chroma 后 load 能自动回填
