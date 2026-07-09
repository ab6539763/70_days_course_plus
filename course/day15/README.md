# Day 15 课件索引

**日期**：2026-07-20（星期一）  
**主题**：大模型原理科普 — Token 计算器  
**需求**：ZL-NA-REQ-015  
**里程碑**：Phase 2 / Sprint 3 开启（Day 15–24）

## 🚀 Sprint 3 启动

恭喜完成 **Sprint 1**（Day 1–14）！今日起进入 **Phase 2 Sprint 3**，从「能对话」迈向「懂用量、控成本、可观测」：

- Day 14 多轮对话 → **Day 15 Token 计数与成本估算**
- Day 16 流式输出（SSE / `async`）
- Day 17–24 检索、工具调用、Agent 编排……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# Token 原理启发式演示
python3 src/day15/token_principle_demos.py

# API usage 与本地估算对比
python3 src/day15/token_counter_demo.py

# CLI 助手 + /tokens 命令
NEXUS_LLM_MOCK=1 python3 src/day15/assistant_token_demo.py

# 交互式（真实使用）
NEXUS_LLM_MOCK=1 python3 src/chat/cli_assistant.py

# 单元测试
python3 -m pytest tests/day15/ -v
```

## 今日交付物

- [x] `llm/token_counter.py` — `estimate_tokens`、`TokenCounter`、`TokenSessionTracker`、`TokenUsage`
- [x] `chat/cli_assistant.py` — `/tokens` 命令、`track_tokens` 集成
- [x] `src/day15/*` 演示脚本
- [x] `tests/day15/test_token_counter.py`
- [x] Day 15 全套课件（29 篇）

## 上下文链

```
Day 5 parse_chat_completion → usage 字段
Day 14 ChatAssistant 多轮历史 → Day 15 量化「记忆代价」
Day 15 Token 计数 → Day 16 流式输出与首 token 延迟
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | Token 计数详解 | 深度专题 |
| 12-14 | 练习册 / tiktoken 扩展 / 成本治理案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day5 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | 大模型原理讲义 / 企业实践 / Sprint3 开启 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **双轨计量**：API `usage` 为权威；本地 `estimate_tokens` 为发送前预警  
2. **启发式 MVP**：CJK 约 1 字 1 token，英文约 4 字符 1 token；不引入 `tiktoken` 依赖  
3. **会话累计**：`TokenSessionTracker` 跨轮累加，暴露多轮上下文膨胀问题  
4. **成本透明**：`DEFAULT_INPUT_PRICE_PER_M` / `DEFAULT_OUTPUT_PRICE_PER_M` 可配置  
5. **非侵入集成**：`ChatAssistant(track_tokens=True)` 可选开关，不影响 Day 14 契约

## Day 16 预告

明日引入 **流式输出**：`stream=True`、SSE 事件、`async` 超时，让用户「边生成边看见」，并讨论流式场景下的 token 统计时机。
