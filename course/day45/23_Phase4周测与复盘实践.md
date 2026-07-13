# Phase 4 周测与复盘实践

## 实验 1：周测扫描

对全班的 `phase4_quiz.py` 交互得分做简单统计，找出正确率最低的题目。

## 实验 2：错题溯源

针对得分最低的题目，回读对应 Day 的 `11_*详解.md`，写出为什么容易错。

## 实验 3：max_nodes 扫描

```python
for max_nodes in (1, 3, 5, 10, 20):
    workflow = build_dify_workflow(executor, max_nodes=max_nodes)
    print(max_nodes, len(workflow.nodes))
```

记录：`max_nodes` ≥ 工具总数后，节点数不再增加。

## 实验 4：dify_trace 与 mcp_trace 对照

同一 query 分别跑 `mcp_mode=true` 与 `dify_mode=true`，对比两者步数与语义是否一一对应。

## 实验 5：降级演练

`PUT dify-config enabled=false`，确认 chat 立即回退、`dify-export`/`dify-preview` 返回 400。

---

## 报告模板

```markdown
# Phase4 Lab
- 周测得分:
- 错题:
- max_nodes 扫描结论:
- dify_trace vs mcp_trace 对照结论:
```

---

## 常见实验坑

- 忘记先跑 `pytest tests/day45/` 确认环境正常再做手工实验
- 用旧 session_id 导致历史干扰对比结果
- 混淆 `dify-preview`（不落盘）与 `dify-config`（落盘）两个 API

---

## 实验 6：Phase 4 全景回顾

运行 `python3 src/day45/phase4_review.py`，逐条对照 Day39-44 的核心类名是否能脱口而出。

---

## 实验 7：文档贡献

向 `17_Dify_API速查手册.md` 提交一条 Windows PowerShell 版本的 curl 示例。

---

## 实验 8：合规审计表

| query | dify_trace 事件数 | 是否含敏感字段 | 合规 |
|-------|-------------------|----------------|------|
| 客服电话多少 | | | |
| 年化收益怎么样 | | | |
