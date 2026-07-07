# Day 30 课件索引

**日期**：2026-08-06（星期四）  
**主题**：增量索引（incremental upsert）  
**需求**：ZL-NA-REQ-030

## 今日交付

- `_incremental_index` — upload 不 reset Chroma
- `_remove_document_by_source` — 同名上传替换
- `chroma_store.delete_by_ids / delete_by_source`
- `index_mode` / `last_incremental_at` 状态字段
- `tests/day30/` 16 项

```bash
PYTHONPATH=src python3 src/day30/incremental_demo.py
PYTHONPATH=src pytest tests/day30/ -q
```

## 关键流程

Day 29 全量 upsert → Day 30 **upload 增量**：仅 upsert 新文档 chunk，rebuild 仍全量。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day30/incremental_demo.py
python3 src/day30/incremental_api_demo.py
python3 -m pytest tests/day30/ -v
```

## 设计决策

1. **upload 默认 incremental=True**  
2. **rebuild 仍 _rebuild_index + reset**  
3. **词表扩张时回退全量 upsert（不 reset）**  
4. **评估路径仍用内存 EmbeddingRetriever**  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_增量索引详解 | 专题 |
| 22_knowledge_incremental精读 | 源码 |
| 27_Day31预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
```
