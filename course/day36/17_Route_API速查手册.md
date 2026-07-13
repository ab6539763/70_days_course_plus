# 自适应路由（Query Router） API 速查手册

## GET /api/knowledge/route-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/route-config | jq .
```

## PUT /api/knowledge/route-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": true}'
```

关闭本日新增能力：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}'
```

## POST /api/knowledge/route-preview

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/route-preview \
  -H 'Content-Type: application/json' \
  -d '{"query": "测试问题"}' | jq .
```

## status 中的 route_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.route_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store

store = get_knowledge_store()
cfg = store.get_route_config()
cfg.enabled = True
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | 配置字段越界或非法 |
| 200 | 成功并持久化 |

## 核心类

- `RoutingRetriever` — 见 `rag/query_router.py`
