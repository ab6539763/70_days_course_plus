# 企业案例集：Supervisor 多 Agent 委派

## 案例 1：客服电话查询

**场景**：「客服电话多少」
**处理**：委派 faq_worker → faq_lookup 工具

## 案例 2：产品收益咨询

**场景**：「年化收益怎么样」
**处理**：委派 rag_worker → rag_search 工具

## 案例 3：模糊归纳请求

**场景**：「帮我总结一下理财产品」
**处理**：委派 intent_worker → intent_classify 工具

## 案例复盘模板

| 日期 | 变更 | 影响 | 备注 |
|------|------|------|------|
| — | 上线 supervisor_mode | — | 配合灰度开关 |

## 与客服话术联动

客服培训重点：解释「机器人这次是怎么决定调用哪个工具的」，对应 `supervisor_trace` 里的 thought 字段。

## Incident 降级预案

怀疑新逻辑引入回归时，`PUT /api/agent/supervisor-config` 将 `enabled` 置为 `false`，立即回退到 Day 42 行为。
