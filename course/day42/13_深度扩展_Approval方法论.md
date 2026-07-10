# 深度扩展：人工审批工作流方法论

## 1. 问题定义

合规要求：涉及具体收益率数字的回答，必须有人工复核后才能发给客户，但当前 chat 接口是全自动直出。

## 2. 设计取舍

在 StateGraph 的 tool_runner 之后插入 human_approval 节点：命中 require_rag_approval 规则时中断执行并返回 checkpoint_id，人工调用 approval-resume 携带 approved/comment 后流程续跑。

## 3. 与上一日的关系

Day41 让节点图可编排；Day42 在图里加入人工审批卡点，管住高风险 RAG 输出。

## 4. 可观测性设计

每一步决策都落进 `approval`，字段设计遵循「thought（为什么）+ 动作（做什么）+ observation（结果）」三元组，方便审计与教学复盘。

## 5. 失败模式

| 现象 | 诊断 |
|------|------|
| 决策总是选同一个工具 | mock 路由规则过于粗糙，需要更细的关键词表 |
| 步数经常打满上限 | 上限设置过低，或工具返回信息不足以收敛 |
| chat 开启后行为无变化 | 忘记同时把配置 `enabled` 打开 |

## 6. 与真实大模型 function-calling 的差异

生产环境通常让大模型自己决定调用哪个工具（true function-calling）；本课在 `NEXUS_LLM_MOCK=1` 下用规则/关键词模拟这一决策，保证测试确定性，同时保留切换到真实模型的接口形状。

## 7. 推荐阅读

- ReAct: Synergizing Reasoning and Acting in Language Models
- LangChain AgentExecutor 官方文档

## 8. 实验设计模板

固定输入集合，对比 `approval_mode` 开/关两种模式下的响应差异，记录延迟与结果准确率。

## 9. 案例：企业级 Agent 平台的分层

```
Stage0: 工具注册（本课 ToolRegistry/StructuredTool）
Stage1: 决策/路由（本课 ApprovalWorkflowGraph）
Stage2: 可观测 trace（本课 approval）
Stage3: 人工干预 / 多 Agent 协作（Day42/43）
Stage4: 协议化外部工具接入（Day44 MCP）
```

## 10. 数学/工程小结

配置项数量与可维护性成反比，建议每个新配置字段都要有明确的默认值与 `validate()` 边界，避免运维猜测。
