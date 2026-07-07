# Day 3 课件索引

**日期**：2026-07-08（星期三）  
**主题**：流程控制 — if/elif/else 与循环  
**Sprint**：Sprint 1 — CLI 工具链（第 3 天）  
**预计学时**：6-8 小时

---

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1 | [00_旁白解读.md](00_旁白解读.md) | 平台 CLI 骨架主线 |
| 2 | [01_企业背景与今日任务.md](01_企业背景与今日任务.md) | 站会、任务 |
| 3 | [02_需求文档.md](02_需求文档.md) | ZL-NA-REQ-003 |
| 4 | [03_架构设计.md](03_架构设计.md) | CLI Shell 架构 |
| 5 | [04_流程图与示意图.md](04_流程图与示意图.md) | 流程图 |
| 6 | [05_课堂笔记_上午.md](05_课堂笔记_上午.md) | if/elif/else |
| 7 | [06_课堂笔记_下午.md](06_课堂笔记_下午.md) | while/for、实操 |
| 8 | [07_晚自习.md](07_晚自习.md) | LeetCode 导读 |
| 9 | [08_作业.md](08_作业.md) | 课后作业 |
| 10 | [09_作业答案.md](09_作业答案.md) | 参考答案 |
| 11 | [10_常见问题与排错指南.md](10_常见问题与排错指南.md) | FAQ |
| 12 | [11_讲师补充阅读.md](11_讲师补充阅读.md) | 选修 |

## 配套代码

```bash
cd nexus-agent-platform
python src/day03/platform_cli.py          # 平台 CLI 主菜单
python src/day03/guess_number.py          # 猜数字游戏
python src/day03/multiplication_table.py  # 九九乘法表
```

## 今日交付物

- [x] `platform_cli.py` — NexusAgent 平台 CLI 骨架（整合 Day 1/2）
- [x] 批量清洗 `sample_docs/`（for 循环）
- [x] 猜数字游戏、九九乘法表

## 上下文链

```
Day 1  personal_info_card  ──┐
Day 2  text_cleaner       ──┼──> Day 3  platform_cli（统一入口）
Day 3  if/while/for       ──┘
         │
         ▼
Day 4  列表管理待办事项
```
