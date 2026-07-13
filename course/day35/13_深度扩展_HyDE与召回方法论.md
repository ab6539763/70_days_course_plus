# 深度扩展：多查询扩展（Query Expansion / HyDE）方法论

## 1. 问题定义

质检发现「理财安全吗」这类模糊问句，单条 query 召回经常漏掉真正相关的 chunk，Recall 不够宽。

## 2. 设计取舍

引入 QueryExpander：把一条问句用模板/HyDE mock 拓展成多条候选 query，ExpandingRetriever 多路并发召回后按 chunk_id 去重合并，再进入既有的 rerank → citations 管线。

## 3. 与上一日的关系

Day 34 让回答有据可查；Day 35 让检索更广更全 — 一条问句拓展成多条 query 再合并召回。

## 4. 可观测性设计

`expansion_config` 与 status 接口对外暴露当前策略，便于运维排障与教学演示。

## 5. 失败模式

| 现象 | 诊断 |
|------|------|
| 新逻辑总是不生效 | 检查 `ExpansionConfig.enabled` 是否为 true |
| 关闭后行为异常 | 应完全回退到 Day 34 逻辑，若仍异常需排查缓存 |
| 效果不明显 | mock 规则与业务分布不匹配，需要更贴合的规则表 |

## 6. 与真实模型的差异

生产环境通常用真实模型完成本日等价能力；本课在 `NEXUS_LLM_MOCK=1` 下用规则模拟，保证测试确定性，同时保留切换到真实模型的接口形状。

## 7. 推荐阅读

- 相关检索增强技术公开资料
- 平台既有 Day 34 实现作为对照

## 8. 实验设计模板

固定输入集合，对比 `ExpansionConfig.enabled` 开/关两种模式下的响应差异，记录延迟与结果准确率。

## 9. 案例：企业级 RAG 管线的分层

```
Stage0-34: 既有检索/生成管线
Stage35: 多查询扩展（Query Expansion / HyDE）
Stage36+: 后续增强
```

## 10. 工程小结

配置项数量与可维护性成反比，建议每个新配置字段都要有明确默认值与 `validate()` 边界。
