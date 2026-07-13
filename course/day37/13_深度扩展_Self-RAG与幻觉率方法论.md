# 深度扩展：Self-RAG 答案校验方法论

## 1. 问题定义

合规部反馈：虽然每条回答都带了 citations，但 LLM 仍偶发「引用是 A、回答是 B」的答非所问。

## 2. 设计取舍

实现 RuleBasedAnswerValidator，在 chat API 返回前校验 reply 与 citations 的 token 重合度打分；分数低于 min_score 且 refuse_on_fail 时拒答。

## 3. 与上一日的关系

Day 36 让管线更省；Day 37 让回答更准 — 生成后校验 citations 是否真的支撑 reply。

## 4. 可观测性设计

`validation_config` 与 status 接口对外暴露当前策略，便于运维排障与教学演示。

## 5. 失败模式

| 现象 | 诊断 |
|------|------|
| 新逻辑总是不生效 | 检查 `ValidationConfig.enabled` 是否为 true |
| 关闭后行为异常 | 应完全回退到 Day 36 逻辑，若仍异常需排查缓存 |
| 效果不明显 | mock 规则与业务分布不匹配，需要更贴合的规则表 |

## 6. 与真实模型的差异

生产环境通常用真实模型完成本日等价能力；本课在 `NEXUS_LLM_MOCK=1` 下用规则模拟，保证测试确定性，同时保留切换到真实模型的接口形状。

## 7. 推荐阅读

- 相关检索增强技术公开资料
- 平台既有 Day 36 实现作为对照

## 8. 实验设计模板

固定输入集合，对比 `ValidationConfig.enabled` 开/关两种模式下的响应差异，记录延迟与结果准确率。

## 9. 案例：企业级 RAG 管线的分层

```
Stage0-36: 既有检索/生成管线
Stage37: Self-RAG 答案校验
Stage38+: 后续增强
```

## 10. 工程小结

配置项数量与可维护性成反比，建议每个新配置字段都要有明确默认值与 `validate()` 边界。
