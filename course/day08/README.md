# Day 8 课件索引

**日期**：2026-07-13（星期一）  
**主题**：面向对象编程（上）— class、对象、ChatMessage  
**Sprint**：Sprint 2 启动（Day 8-14 对话能力）

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1-4 | 旁白/企业/需求/架构 | Sprint 2 与 OOP 背景 |
| 5-6 | 上午/下午课堂笔记 | 类与对象、ChatMessage 实操 |
| 7-19 | 作业/扩展/速查 | 巩固 |

## 配套代码

```bash
cd nexus-agent-platform
python3 src/day08/oop_demos.py
python3 src/day08/message_cli.py
python3 -m pytest tests/day08/ -v
```

## 今日交付物

- [x] `src/models/message.py` — `ChatMessage` 类
- [x] `src/day08/message_history.py` — 消息历史容器
- [x] `src/day08/message_cli.py` — 消息实验室 CLI
- [x] `src/day08/contact_class.py` — Contact 类（dict 升级 OOP 示例）

## 上下文链

```
Day 7 通讯录 dict → Day 8 ChatMessage 类 + MessageHistory  ← 今日
Day 9            BaseModel 抽象类体系
Day 14           阶段项目一：命令行多轮对话助手
```
