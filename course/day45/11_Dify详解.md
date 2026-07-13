# Dify 工作流对接详解（Day 45 专题）

## 1. 问题定义

低代码工作流对接 = 把内部工具能力**导出**成外部平台（Dify）能理解的图结构（节点 + 边），同时把内部运行 trace **映射**成外部平台熟悉的日志语义，双向对齐但不重复实现。

## 2. Dify DSL 教学子集

| 字段 | 含义 |
|------|------|
| app.name | 工作流名称 |
| app.mode | 固定为 "workflow" |
| workflow.graph.nodes | 节点列表，每个含 id + data.type/title |
| workflow.graph.edges | 边列表，source → target |

```mermaid
flowchart LR
    TE[ToolExecutor] --> B[build_dify_workflow]
    B --> DSL[DifyWorkflow]
    DSL --> JSON[app + workflow.graph]
```

## 3. build_dify_workflow 逻辑

1. 取 `registry.list_tools()[:max_nodes]`
2. `include_start_end=True` 时先放一个 `start` 节点
3. 每个工具生成一个 `tool_<name>` 节点，`data` 含 description + parameters
4. 顺序连边：`start → tool1 → tool2 → ... → end`

## 4. map_steps_to_dify_trace 与 McpStep

`McpRunner.invoke` 的四阶段（discover/route/call/answer）分别映射：

| McpStep.phase | DifyTraceEvent.node_type |
|---------------|--------------------------|
| discover | start |
| route | tool |
| call | tool |
| answer | end |

## 5. 与 Chat 集成

`api/chat.py` 在 `dify_mode=true` 且配置 `enabled` 时调用 `DifyRunner.invoke`，把返回的 `dify_trace` 填入 `ChatResponse.dify_trace`。

## 6. 前端展示（展望）

未来可加 `msg__dify` 组件，把 `dify_trace` 渲染成小型流程图，帮助运营理解一次调用具体走了哪些节点。

---

## 7. 与合规的关系

| 审计项 | dify_trace 提供 |
|--------|-----------------|
| 调用了哪个工具 | node title |
| 输入参数 | inputs |
| 返回结果 | outputs |
| 执行顺序 | node_id 中的 step 序号 |

---

## 8. 配置调参

| 场景 | max_nodes |
|------|-----------|
| 小型演示 | 3-5 |
| 默认 | 10 |
| 全量导出（工具很多） | 20-50 |

---

## 9. 常见误区

| 误区 | 正解 |
|------|------|
| DifyRunner 重新实现了路由逻辑 | 内部持有 McpRunner，直接复用其 invoke |
| dify_trace 与 mcp_trace 是两份独立数据 | dify_trace 由 mcp_trace 一一映射而来 |
| 导出的 DSL 能直接导入生产 Dify | 当前为教学子集，字段远比真实 Dify DSL 简化 |
