# Dify API 速查手册

## GET dify-config

```bash
curl -s http://127.0.0.1:8000/api/agent/dify-config | jq .
```

响应：

```json
{
  "enabled": true,
  "workflow_name": "nexus-agent-workflow",
  "include_start_end": true,
  "mock_routing": true,
  "use_session_history": true,
  "return_dify_trace": true,
  "max_nodes": 10
}
```

## PUT dify-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "workflow_name": "nexus-agent-workflow",
    "include_start_end": true,
    "mock_routing": true,
    "use_session_history": true,
    "return_dify_trace": true,
    "max_nodes": 10
  }'
```

关闭 Dify 对接：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/agent/dify-config \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false, "workflow_name": "nexus-agent-workflow", "include_start_end": true, "mock_routing": true, "use_session_history": true, "return_dify_trace": true, "max_nodes": 10}'
```

## POST dify-export

```bash
curl -s -X POST http://127.0.0.1:8000/api/agent/dify-export | jq '.workflow.graph.nodes'
```

## POST dify-preview

```bash
curl -s -X POST http://127.0.0.1:8000/api/agent/dify-preview \
  -H 'Content-Type: application/json' \
  -d '{"query":"客服电话多少"}' | jq .
```

## chat 集成

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"客服电话多少","dify_mode":true}' | jq '.dify_trace'
```

## status 中的 dify_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.dify_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from agent.dify_config import DifyConfig

store = get_knowledge_store()
store.set_dify_config(DifyConfig(workflow_name="custom-workflow", max_nodes=5))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | max_nodes 越界或 workflow_name 为空 |
| 400 | dify_config.enabled=false 时调用 export/preview |
| 200 | 成功 |

## 常量

- `DIFY_NODE_START` = `"start"`
- `DIFY_NODE_TOOL` = `"tool"`
- `DIFY_NODE_END` = `"end"`
