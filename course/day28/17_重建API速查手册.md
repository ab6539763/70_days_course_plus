# Day 28 重建 API 速查手册

## POST /api/knowledge/rebuild

默认 body：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{}' | jq .
```

仅 uploads：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"include_sample_docs": false}' | jq .
```

评估 + 重建：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"include_sample_docs": true, "apply_best_config": true}' | jq .
```

## 响应字段

```json
{
  "documents_before": 3,
  "chunks_before": 12,
  "documents_after": 3,
  "chunks_after": 8,
  "sources_processed": 3,
  "chunk_config": {"name": "wide", "chunk_size": 400, ...},
  "source_files": ["raw_faq.txt", "..."],
  "rebuilt_at": "2026-08-04T12:00:00Z",
  "sessions_cleared": 0,
  "message": "知识库已按当前 chunk_config 全量重建"
}
```

## GET /api/knowledge/status

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.last_rebuilt_at, .chunk_count'
```

## Python 直接调用

```python
from rag.knowledge_store import KnowledgeStore
from rag.knowledge_rebuild import rebuild_store

store = KnowledgeStore.bootstrap_from_sample_docs()
report = rebuild_store(store)
print(report.chunks_before, "->", report.chunks_after)
```

## 错误排查

| 现象 | 可能原因 |
|------|----------|
| sources_processed=0 | 无 sample 且无 uploads |
| chunks_after=0 | 源文件全空 |
| 500 | store 路径不可写 |

---

## curl 完整示例集

```bash
# 1. 查看重建前状态
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_count,.last_rebuilt_at,.chunk_config'

# 2. 标准重建
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"include_sample_docs":true,"apply_best_config":false}' | jq .

# 3. 评估驱动重建
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \
  -H 'Content-Type: application/json' \
  -d '{"apply_best_config":true}' | jq '.chunk_config,.chunks_after,.rebuilt_at'

# 4. 重建后抽测 chat
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"投资有风险吗","session_id":"post-rebuild-check"}' | jq .
```

## 响应字段详解

| 字段 | 教学关注点 |
|------|------------|
| chunks_before/after | 发布是否改变索引规模 |
| source_files | 与磁盘源是否一致 |
| sessions_cleared | 是否通知用户重新对话 |
| chunk_config | 实际生效的重建配置快照 |
| message | 人类可读摘要，可打日志 |
