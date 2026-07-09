# Executor API 速查（Day 40）

```
GET  /api/agent/executor-config
PUT  /api/agent/executor-config
POST /api/agent/executor-preview
POST /api/chat  { "executor_mode": true }
```

响应字段：`executor_trace`、`tools_used`、`intermediate_steps`（preview）
