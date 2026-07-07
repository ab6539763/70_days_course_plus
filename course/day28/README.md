# Day 28 课件索引

**日期**：2026-08-04（星期二）  
**主题**：知识库全量重建（rebuild）  
**需求**：ZL-NA-REQ-028

## 今日交付

- `rag/knowledge_rebuild.py` — collect_source_files / rebuild_store
- `POST /api/knowledge/rebuild` — 全量重建 API
- `apply_best_config` — 评估后自动应用最优分块
- `last_rebuilt_at` 持久化
- `frontend` 全量重建按钮
- `tests/day28/` 14 项

```bash
PYTHONPATH=src python3 src/day28/rebuild_demo.py
PYTHONPATH=src pytest tests/day28/ -q
```

## 关键流程

Day 27 选出 chunk_config → Day 28 **rebuild** 让整个库统一到该配置。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day28/rebuild_demo.py
python3 src/day28/rebuild_api_demo.py
python3 -m pytest tests/day28/ -v
```

## 设计决策

1. **双源扫描**：sample_docs 保证开箱即用，uploads 承载运营文档  
2. **uploads 优先**：同名文件以用户上传为准  
3. **apply_best_config**：evaluate + rebuild 一键发布  
4. **sessions_cleared**：重建后编排器使用新索引  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_知识库重建详解 | 专题 |
| 22_knowledge_rebuild精读 | 源码 |
| 27_Day29向量库预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day28/rebuild_api_demo.py
```
