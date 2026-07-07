# Day 27 调参 API 速查手册

## 环境

```bash
export PYTHONPATH=src NEXUS_LLM_MOCK=1
uvicorn api.app:create_app --factory --reload
```

## GET /api/knowledge/chunk-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/chunk-config | jq .
```

响应示例：

```json
{
  "chunk_size": 200,
  "overlap": 40,
  "strategy": "auto",
  "name": "default"
}
```

## PUT /api/knowledge/chunk-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/chunk-config \
  -H 'Content-Type: application/json' \
  -d '{
    "chunk_size": 400,
    "overlap": 60,
    "strategy": "auto",
    "name": "wide"
  }' | jq .
```

错误示例（422）：

```bash
curl -s -X PUT ... -d '{"chunk_size":50,"overlap":50,"strategy":"auto","name":"x"}'
```

## POST /api/knowledge/evaluate

预设评估：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"use_presets": true}' | jq .
```

自定义配置：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "use_presets": false,
    "configs": [
      {"chunk_size": 180, "overlap": 30, "strategy": "auto", "name": "lab1"}
    ]
  }' | jq .best_config
```

## GET /api/knowledge/status

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.chunk_config, .chunk_count'
```

## Python TestClient 片段

```python
from fastapi.testclient import TestClient
from api.app import create_app

client = TestClient(create_app())
assert client.post("/api/knowledge/evaluate", json={"use_presets": True}).status_code == 200
```

## 错误码

| 状态码 | 场景 |
|--------|------|
| 422 | validate 失败、请求体非法 |
| 500 | 样例缺失、评估无结果 |
