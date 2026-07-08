# Day 7 课件索引

**日期**：2026-07-12（星期日）  
**主题**：第一周复习 + 通讯录管理系统 + 周测  
**Sprint**：Sprint 1 收官（Day 2-7）

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1-4 | 旁白/企业/需求/架构 | Sprint 1 收官背景 |
| 5-6 | 上午复习 / 下午实操 | Day 1-6 串讲 + 通讯录开发 |
| 7-17 | 周测/作业/扩展 | 巩固与验收 |

## 配套代码

```bash
cd nexus-agent-platform
python3 src/day07/week1_quiz.py          # 第一周周测
python3 src/day07/contacts_manager.py    # 通讯录 CLI
python3 -m pytest tests/day07/ -v
```

## 今日交付物

- [x] `contact_service.py` — 通讯录业务函数层
- [x] `contacts_manager.py` — 完整 CLI 应用
- [x] `week1_quiz.py` — 10 题周测
- [x] `utils` 扩展 `validate_phone`、`format_contact_line`
- [x] Sprint 1 收官：CLI 工具链第一阶段完成

## 上下文链

```
Day 6 utils 重构 → Day 7 综合项目（通讯录）+ 周测  ← 今日
Day 8           面向对象 ChatMessage 类
```
