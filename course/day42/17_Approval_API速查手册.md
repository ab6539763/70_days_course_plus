# Approval API 速查（Day 42）

```
GET  /api/agent/approval-config
PUT  /api/agent/approval-config
POST /api/agent/approval-preview
POST /api/agent/approval-resume
POST /api/chat  { "approval_mode": true }
```

响应字段：`approval`、`graph_trace`、`checkpoint_id`（中断时）
