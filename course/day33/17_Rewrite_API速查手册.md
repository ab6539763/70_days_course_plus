# Rewrite API 速查手册

## GET rewrite-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/rewrite-config | jq .
```

响应：

```json
{
  "enabled": true,
  "max_rewrite_len": 20,
  "model": "mock"
}
```

## PUT rewrite-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rewrite-config \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "max_rewrite_len": 20,
    "model": "mock"
  }'
```

关闭改写：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rewrite-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false, "max_rewrite_len": 20, "model": "mock"}'
```

## status 中的 rewrite_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.rewrite_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.rewrite_config import RewriteConfig

store = get_knowledge_store()
store.set_rewrite_config(RewriteConfig(enabled=True, max_rewrite_len=15))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | pool 越界或 model 非法 |
| 200 | 成功并持久化 |

## 常量

- `MODEL_MOCK` = `"mock"`
