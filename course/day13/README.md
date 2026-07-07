# Day 13 课件索引

**日期**：2026-07-18（星期六）  
**主题**：装饰器与异步 — API 重试与超时机制  
**需求**：ZL-NA-REQ-013  
**Sprint**：Sprint 2 第 6 天

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 装饰器基础（无参、带参、functools.wraps）
python3 src/day13/decorator_demos.py

# retry 装饰器（模拟 429 限流后成功）
python3 src/day13/retry_demos.py

# asyncio 入门预习
python3 src/day13/async_demos.py

# 弹性 LLM 客户端（Mock + 503 重试）
NEXUS_LLM_MOCK=1 python3 src/day13/resilient_client_demo.py

# 单元测试
python3 -m pytest tests/day13/ -v
```

## 今日交付物

- [x] `llm/retry.py` — `retry`、`with_timeout`、`RetryPolicy`、`is_retryable_error`
- [x] `llm/resilient_client.py` — `ResilientLLMClient` 包装 `LLMClient.complete`
- [x] `src/day13/*_demos.py` — 装饰器、重试、异步、弹性客户端演示
- [x] Day 13 单元测试与课件

## 上下文链

```
Day 12 LLMClient.complete（单次 HTTP）→ Day 13 装饰器重试/超时  ← 今日
Day 13 ResilientLLMClient → Day 14 cli_assistant 多轮对话
Day 16 流式输出将改用异步超时（替代 ThreadPoolExecutor）
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | 装饰器与重试详解 | 深度专题 |
| 12-14 | 练习册 / 异步扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | 装饰器讲义 / 重试实践 / Sprint2 回顾 / 精读 / Lab | 进阶实操 |

## 关键设计决策

1. **装饰器工厂**：`@retry(max_attempts=3)` 用三层嵌套实现带参装饰器  
2. **指数退避**：`base_delay × backoff_factor^(attempt-1)`，上限 `max_delay`  
3. **可重试判定**：429、500、502、503、504；**不重试** ConfigError、401 等客户端错误  
4. **组合顺序**：内层 `with_timeout`，外层 `retry`——每次重试重新计时  
5. **functools.wraps**：保留被装饰函数的 `__name__` 与文档，便于调试与测试

## Day 14 预告

明日实现 `cli_assistant`：**多轮对话** CLI，调用 `ResilientLLMClient.chat()`，维护 `messages` 历史，体验「能聊、能扛抖动」的终端助手。
