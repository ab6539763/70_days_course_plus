# Rewrite API 速查手册

## GET expansion-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/expansion-config | jq .
```

响应：

```json
{
  "enabled": true,
  "max_citations": 20,
  "model": "mock"
}
```

## PUT expansion-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/expansion-config \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "max_citations": 20,
    "model": "mock"
  }'
```

关闭改写：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/expansion-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false, "max_citations": 20, "model": "mock"}'
```

## status 中的 citation_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.citation_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import ExpansionConfig

store = get_knowledge_store()
store.set_citation_config(ExpansionConfig(enabled=True, max_citations=15))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | pool 越界或 model 非法 |
| 200 | 成功并持久化 |

## 常量

- `MODEL_MOCK` = `"mock"`
