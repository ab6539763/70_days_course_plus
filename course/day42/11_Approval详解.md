# 人工审批工作流详解（Day 42 专题）

## 1. 卡点

`rag_search` 结果默认需 `human_approval` 节点审核（FAQ 直答跳过）。

## 2. 中断恢复

`mock_auto_approve=false` 时生成 `checkpoint_id`；`approval-resume` 携带 approved 继续。

## 3. 可观测

`graph_trace` 含 `human_approval` 节点；`approval.status` 为 pending/approved/rejected。
