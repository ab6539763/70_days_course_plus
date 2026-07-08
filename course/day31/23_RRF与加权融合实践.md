# RRF 与加权融合实践

## 实验 1：手工 RRF 计算

设 `rrf_k=60`。

| doc | keyword rank | vector rank | RRF 分 |
|-----|--------------|-------------|--------|
| A | 1 | - | 1/61 |
| B | 3 | 1 | 1/63+1/61 |
| C | - | 2 | 1/62 |

排序 B > C > A（可课堂验算）。

## 实验 2：weighted 权重扫描

```python
for kw in (0.2, 0.35, 0.5, 0.7):
    cfg = RetrievalConfig(mode="hybrid", fusion="weighted",
                          keyword_weight=kw, vector_weight=1-kw)
    # 对 HYBRID_QUERIES 打 hit@1
```

记录：号码 query 在 kw≥0.5 时 hit@1 提升。

## 实验 3：fusion A/B

同库同样 query，对比 weighted 与 rrf 的 top-3 重叠率 Jaccard。

## 实验 4：pool 消融

临时改 `pool=max(top_k*2,8)` 与 `top_k*8`，观察号码 query top-1 是否变化。

## 实验 5：单路对照

`mode=keyword` vs `mode=vector` 全量跑 `HYBRID_QUERIES`，填表。

---

## 报告模板

```markdown
# Fusion Lab
- query: 13900001111
- weighted top1:
- rrf top1:
- 结论:
```

---

## 常见实验坑

- 未 `set_retrieval_config` 后重建 `as_rag_service`  
- 忘记 `store.save()` 导致 API 与本地不一致  
- 用绝对分数比较两路 — 应看排名或 norm 后分数
