# 企业案例集：MCP 协议与工具生态

## 案例 1：客服电话查询

**场景**：「客服电话多少」
**处理**：tools/list 发现 faq_lookup → tools/call 执行 → mcp_trace 记录四阶段

## 案例 2：产品收益咨询

**场景**：「年化收益怎么样」
**处理**：路由到 rag_search，走同一套 MCP 调用管线

## 案例 3：未来切换真实 MCP Server

**场景**：把 NexusMcpServer 换成外部进程/HTTP MCP 端点
**处理**：McpClient/McpRunner 接口不变，只替换 transport 层

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 mcp_mode | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `mcp_trace` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT /api/agent/mcp-config` 将 `enabled` 置为 `false`，立即回退到 Day 43 行为。
