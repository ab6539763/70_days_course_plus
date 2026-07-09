# Phase 3 第六日总结（Day 25–30）

| Day | 主题 |
|-----|------|
| 25 | KnowledgeStore |
| 26 | 多格式解析 |
| 27 | 调参 A/B |
| 28 | rebuild |
| 29 | Chroma |
| 30 | 增量索引 |

Day 30 完成「运营级」上传体验；Day 31 混合检索提升问答质量。

---

## Day25–30 技能树

```
ingest → parse → chunk → [evaluate] → rebuild
                              ↓
                         Chroma 持久化 (D29)
                              ↓
                         incremental (D30)
                              ↓
                         hybrid (D31 预告)
```

---

## 版本线

| 版本 | 里程碑 |
|------|--------|
| 0.25 | 知识库 MVP |
| 0.28 | rebuild 发布 |
| 0.29 | Chroma |
| 0.30 | incremental |

---

## 团队复盘三句话

1. 扩张 reset 是正确性不是偷懒  
2. mock reset 测试是发布门禁  
3. 明日混合检索别忘 Day27 评估方法论
