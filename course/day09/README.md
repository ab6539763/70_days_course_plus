# Day 9 课件索引

**日期**：2026-07-14（星期二）  
**主题**：面向对象（下）— 继承、抽象类、BaseModel 体系  
**Sprint**：Sprint 2 第 2 天

## 配套代码

```bash
cd nexus-agent-platform
python3 src/day09/inheritance_demos.py
python3 src/day09/polymorphism_demo.py
python3 -m pytest tests/day09/ -v
```

## 今日交付物

- [x] `models/llm_base.py` — BaseModel 抽象基类
- [x] `models/model_config.py` — ModelConfig 配置模型
- [x] `models/contact.py` — Contact 迁入 models 并继承 BaseModel
- [x] `ChatMessage` 重构为 BaseModel 子类

## 上下文链

```
Day 8 ChatMessage 类 → Day 9 BaseModel 抽象体系  ← 今日
Day 10 包结构重组与异常
Day 12 首次 LLM API（使用 ModelConfig）
```

## 学习路径

| 序号 | 文件 | 内容 |
|------|------|------|
| 1-4 | 旁白/企业/需求/架构 | OOP 下背景 |
| 5-6 | 上午/下午课堂笔记 | 继承、ABC、实操 |
| 11,20 | OOP 详解 / 代码走查 | 深度阅读 |
| 21 | 知识竞赛题库 | 复盘自测 |
| 8-9 | 作业与答案 | 课后巩固 |

## 评审要点

1. 三个模型类均继承 BaseModel，pytest 全绿  
2. 能演示 `polymorphism_demo` 的 ModelRegistry  
3. 能说明 `ensure_valid` 与 `from_dict_safe` 的使用场景差异  
4. Day 8 回归测试无破坏（重构安全）

## 预计学时

上午 3h（理论 + inheritance_demos）+ 下午 3h（实操 + pytest）+ 晚自习 1.5h（竞赛 + 作业）≈ 7.5h，与课程每日 6–8 小时安排一致。
