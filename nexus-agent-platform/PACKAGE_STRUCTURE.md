# NexusAgent 包结构说明

**版本**：v0.28.0（Day 28 知识库重建）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-028

## Day 28 新增

```
src/rag/knowledge_rebuild.py
  collect_source_files()   # sample_docs + uploads
  rebuild_store()          # 全量清空再分块
  rebuild_with_best_config()
src/day28/
  rebuild_demo.py
  rebuild_api_demo.py
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/rebuild` | 全量重建，可选 apply_best_config |

`store.json` 新增 `last_rebuilt_at` 字段。

## 重建源

1. `data/knowledge/uploads/` — 用户上传  
2. `day02/sample_docs/` — 内置样例（可 include_sample_docs=false 跳过）  

同名文件 uploads 优先。
