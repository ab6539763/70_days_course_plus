# Rerank API 速查手册

## GET rerank-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/rerank-config | jq .
```

响应：

```json
{
  "enabled": true,
  "candidate_pool": 20,
  "model": "mock"
}
```

## PUT rerank-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rerank-config \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "candidate_pool": 20,
    "model": "mock"
  }'
```

关闭精排：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rerank-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false, "candidate_pool": 20, "model": "mock"}'
```

## status 中的 rerank_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.rerank_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.rerank_config import RerankConfig

store = get_knowledge_store()
store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=15))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | pool 越界或 model 非法 |
| 200 | 成功并持久化 |

## 常量

- `MODEL_MOCK` = `"mock"`
