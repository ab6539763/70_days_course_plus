# 深度扩展：MCP 协议与工具生态方法论

## 1. 问题定义

SubAgent 的三个工具都是进程内直调，若要接入第三方团队独立维护的工具（甚至跨语言），Supervisor 现有委派方式无法复用；需要一套与厂商无关的协议边界。

## 2. 设计取舍

自研一个符合 MCP（Model Context Protocol）语义的 Server：对外暴露 tools/list（发现工具 schema）与 tools/call（按名调用），McpRunner 按 discover→route→call→answer 四阶段驱动，未来把进程内 Server 换成真实外部 MCP 服务时业务代码无需改动。

## 3. 与上一日的关系

Day43 让 Agent 可协作；Day44 让工具链可扩展 — 用 MCP 协议对接进程外/未来的外部工具。

## 4. 可观测性设计

每一步决策都落进 `mcp_trace`，字段设计遵循「thought（为什么）+ 动作（做什么）+ observation（结果）」三元组，方便审计与教学复盘。

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

固定输入集合，对比 `mcp_mode` 开/关两种模式下的响应差异，记录延迟与结果准确率。

## 9. 案例：企业级 Agent 平台的分层

```
Stage0: 工具注册（本课 ToolRegistry/StructuredTool）
Stage1: 决策/路由（本课 McpRunner）
Stage2: 可观测 trace（本课 mcp_trace）
Stage3: 人工干预 / 多 Agent 协作（Day42/43）
Stage4: 协议化外部工具接入（Day44 MCP）
```

## 10. 数学/工程小结

配置项数量与可维护性成反比，建议每个新配置字段都要有明确的默认值与 `validate()` 边界，避免运维猜测。
