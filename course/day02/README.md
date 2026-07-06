# Day 2 课件索引

**日期**：2026-07-07（星期二）  
**主题**：运算符与字符串  
**Sprint**：Sprint 1 — CLI 工具链  
**预计学时**：6-8 小时

---

## 学习路径

| 序号 | 文件 | 内容 | 建议时间 |
|------|------|------|----------|
| 1 | [00_旁白解读.md](00_旁白解读.md) | 上下文、RAG 预处理主线 | 15 min |
| 2 | [01_企业背景与今日任务.md](01_企业背景与今日任务.md) | 站会、任务分配 | 10 min |
| 3 | [02_需求文档.md](02_需求文档.md) | ZL-NA-REQ-002 | 15 min |
| 4 | [03_架构设计.md](03_架构设计.md) | 文档处理流水线位置 | 20 min |
| 5 | [04_流程图与示意图.md](04_流程图与示意图.md) | 清洗流程图 | 10 min |
| 6 | [05_课堂笔记_上午.md](05_课堂笔记_上午.md) | 运算符详解 | 90 min |
| 7 | [06_课堂笔记_下午.md](06_课堂笔记_下午.md) | 字符串、f-string、实操 | 120 min |
| 8 | [07_晚自习.md](07_晚自习.md) | 复习与预习 | 45 min |
| 9 | [08_作业.md](08_作业.md) | 课后作业 | 90 min |
| 10 | [09_作业答案.md](09_作业答案.md) | 参考答案 | 30 min |
| 11 | [10_常见问题与排错指南.md](10_常见问题与排错指南.md) | FAQ | 随时查阅 |
| 12 | [11_讲师补充阅读.md](11_讲师补充阅读.md) | Prompt 与字符串的关系 | 选修 |

## 配套代码

```bash
cd nexus-agent-platform
python src/day02/text_cleaner.py --help
python src/day02/text_cleaner.py --input src/day02/sample_docs/raw_notice.txt
python src/day02/text_cleaner.py --input src/day02/sample_docs/raw_notice.txt --report
```

## 今日交付物

- [x] `text_cleaner.py` 文本清洗 CLI
- [x] 敏感词替换、空白规范化、大小写统一
- [x] 清洗报告（统计替换次数、字符变化）

## 与 Day 1 的关联

| Day 1 | Day 2 |
|-------|-------|
| `print` / `input` | 字符串方法 + f-string 格式化输出 |
| 个人信息卡片字段拼接 | 清洗后文本格式化报告 |
| `constants.py` | 扩展敏感词表、配置项 |

## 下一天预告

Day 3 学习 **if/elif/else 与循环**，为 `text_cleaner` 增加交互式菜单和批量文件处理模式。
