# 企业案例集：Dify 对接场景

## 案例 1：客服工单预处理流程

**现象**：市场部想要「先查 FAQ，查不到再查产品资料，还查不到转人工」的分支逻辑。
**根因**：当前教学子集只支持线性 `start → tool* → end`，不支持条件分支。
**方案**：导出线性工作流后，在 Dify 画布里手动加 if-else 节点做分支（超出本课 DSL 范围，留给 Dify 原生能力）。
**结果**：核心工具节点由 Nexus 自动生成，分支逻辑由市场部在 Dify 侧维护，分工清晰。

## 案例 2：审计日志对齐

**现象**：运维发现 Dify 侧日志里的节点执行顺序和 Nexus 自己的 `mcp_trace` 对不上号。
**根因**：误关闭了 `return_dify_trace` 或 `return_mcp_trace` 其中一个。
**方案**：检查两个 config 的 `return_*_trace` 均为 true，问题解决。
**结果**：`dify_trace` 与 `mcp_trace` 的 phase→step 映射恢复一致。

## 案例 3：工具太多导出超时

**现象**：`ToolRegistry` 后续注册了 50+ 工具，导出接口响应变慢。
**方案**：`PUT max_nodes=20` 只导出高频工具，其余工具通过 MCP 协议按需接入。
**权衡**：Dify 画布更简洁，但需要额外文档说明"未导出工具仍可通过 MCP 调用"。

## 案例 4：新工具上线零改动

**现象**：新增「工单查询」工具后，市场部担心 Dify 那边要重新配置。
**方案**：新工具注册进 `ToolRegistry` 后，下次调用 `dify-export` 自动包含，无需改 Dify 侧任何配置（除非要手动拖拽新节点到画布）。
**结果**：验证了"工具定义单一来源"的设计价值。

## 案例 5：Incident 降级

**现象**：怀疑 Dify 对接引入了性能回归。
**方案**：`PUT /api/agent/dify-config` 将 `enabled` 设为 `false`，chat 立即回退到不含 dify_trace 的普通模式，30 分钟内确认问题范围。

## 案例 6：Phase 4 周测发现知识漏洞

**现象**：多名学员在"Supervisor 与 MCP 差异"这题上失分。
**工具**：`phase4_quiz.py` 的 `explain` 字段直接给出对比句子，讲师现场补充"进程内 vs 协议化"的板书。
**结果**：错题率从 40% 降到 5%（复训后二测）。

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 dify-export | — | 配合灰度开关 |

## 与客服话术联动

客服/运营培训重点：解释"这份 JSON 就是机器人能用的工具清单，导入 Dify 就能拖拽"。

## 离线评估脚本

```python
for max_nodes in (1, 5, 10, 20):
    workflow = build_dify_workflow(executor, max_nodes=max_nodes)
    print(max_nodes, len(workflow.nodes))
```
