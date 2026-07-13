# Day 42 课件索引

**主题**：人工审批工作流 — human_approval 节点 + checkpoint 中断恢复
**需求**：ZL-NA-REQ-042
**平台版本**：v0.42.0

## 今日交付

| 模块 | 说明 |
|------|------|
| `agent/approval_config.py` | ApprovalConfig — require_rag_approval / mock_auto_approve |
| `agent/approval_checkpoint.py` | 中断检查点存取 |
| `agent/approval_workflow_graph.py` | human_approval 节点 + resume |

| API | 说明 |
|-----|------|
| GET/PUT /api/agent/approval-config | 配置读写 |
| POST /api/agent/approval-preview | 无状态预览，返回 `approval` |
| POST /api/agent/approval-resume | 额外接口 |

`POST /api/chat` + `approval_mode: true` → 响应含 `approval` + graph_trace。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day42/approval_demo.py
python3 src/day42/approval_api_demo.py
python3 -m pytest tests/day42/ -v
```

## 关键流程

Day41 让节点图可编排；Day42 在图里加入人工审批卡点，管住高风险 RAG 输出。

## 验收

`tests/day42/` 16 项全绿；`day42/phase4_approval_review.py` 打印今日交付清单。

---

## 课件生成

```bash
python3 scripts/generate_day42_course.py
```
