# 企业案例集：AgentExecutor 框架工具链

## 案例 1：新增工具零改动

**场景**：运营要求新增「工单查询」工具
**处理**：写一个带类型标注的函数 + @tool 装饰器即可注册，无需改 AgentExecutor 代码

## 案例 2：schema 校验前置

**场景**：工具入参类型不对
**处理**：StructuredTool.to_openai_tool() 导出的 schema 可直接喂给真实模型做 function-calling 校验

## 案例 3：与 ReAct 对比

**场景**：同一问题分别跑 Day39/Day40
**处理**：intermediate_steps 与 agent_trace 结构一致，便于灰度切换

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 executor_mode | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `executor_trace` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT /api/agent/executor-config` 将 `enabled` 置为 `false`，立即回退到 Day 39 行为。
