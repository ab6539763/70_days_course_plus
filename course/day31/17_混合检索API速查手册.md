# 混合检索 API 速查手册

## GET retrieval-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/retrieval-config | jq .
```

响应：

```json
{
  "mode": "hybrid",
  "keyword_weight": 0.35,
  "vector_weight": 0.65,
  "fusion": "weighted",
  "rrf_k": 60
}
```

## PUT retrieval-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/retrieval-config \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "hybrid",
    "fusion": "rrf",
    "keyword_weight": 0.4,
    "vector_weight": 0.6,
    "rrf_k": 60
  }'
```

## status 中的 retrieval_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.retrieval_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, MODE_HYBRID

store = get_knowledge_store()
store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | mode/fusion 非法或 rrf_k<1 |
| 200 | 成功并持久化 |

## 常量

- `MODE_VECTOR` / `MODE_KEYWORD` / `MODE_HYBRID`  
- `FUSION_WEIGHTED` / `FUSION_RRF`
