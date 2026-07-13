# 企业案例集：手写 ReAct Agent

## 案例 1：多轮追问

**场景**：用户先问「客服电话」再问「收益率」
**处理**：同一 session 内两次独立 Thought→Action，agent_trace 分别记录

## 案例 2：工具不存在

**场景**：Thought 选中一个未注册工具名
**处理**：ToolExecutor 抛错，Observation 返回错误文本，Agent 仍能给出兜底回复

## 案例 3：步数超限

**场景**：max_steps=3 但问题需要 4 步
**处理**：第 3 步后强制生成 Final Answer，避免死循环

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 agent_mode | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `agent_trace` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT /api/agent/react-config` 将 `enabled` 置为 `false`，立即回退到 Day 38 行为。
