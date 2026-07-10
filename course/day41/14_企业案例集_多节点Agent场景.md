# 企业案例集：StateGraph 状态图编排

## 案例 1：插桩审计

**场景**：合规要求记录每一步决策节点
**处理**：node_path 直接给出 planner→tool_runner→answer 的完整轨迹

## 案例 2：提前收敛

**场景**：简单问题不需要工具
**处理**：planner 判定后条件边直接跳到 answer，跳过 tool_runner

## 案例 3：为审批铺路

**场景**：Day42 需要在工具执行后插入人工审批
**处理**：只需在 tool_runner 和 answer 之间插入新节点，无需重写整个循环

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 graph_mode | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `graph_trace` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT /api/agent/graph-config` 将 `enabled` 置为 `false`，立即回退到 Day 40 行为。
