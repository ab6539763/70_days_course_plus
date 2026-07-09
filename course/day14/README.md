# Day 14 课件索引

**日期**：2026-07-19（星期日）  
**主题**：阶段项目一 — 命令行多轮对话 AI 助手  
**需求**：ZL-NA-REQ-014  
**里程碑**：Sprint 1 / Phase 1 收官（Day 1–14）

## 🎉 Sprint 1 完成

恭喜完成 **Sprint 1**！从 Day 1 的环境搭建到今日 `cli_assistant`，你已具备：

- Python 基础与 OOP（Day 1–9）
- 包结构与领域模型（Day 10）
- 文档读取与 LLM 单次调用（Day 11–12）
- 重试与弹性客户端（Day 13）
- **多轮对话 CLI 整合交付（Day 14）**

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 交互式多轮对话（真实使用）
NEXUS_LLM_MOCK=1 python3 src/chat/cli_assistant.py

# CI 友好验收脚本
NEXUS_LLM_MOCK=1 python3 src/day14/cli_assistant_demo.py

# 组件演示（不进入交互循环）
NEXUS_LLM_MOCK=1 python3 src/day14/assistant_demos.py

# Sprint 1 能力回顾
python3 src/day14/sprint1_review.py

# 单元测试
python3 -m pytest tests/day14/ -v
```

## 今日交付物

- [x] `chat/cli_assistant.py` — `ChatAssistant`、`run_cli`、`COMMANDS`
- [x] 整合 `ResilientLLMClient`、`MessageHistory`、`ChatMessage`、`ModelConfig`
- [x] 斜杠命令：`/help`、`/exit`、`/quit`、`/clear`、`/history`、`/save`、`/system`
- [x] `run_scripted`（CI）与 `run_interactive`（真实使用）
- [x] `src/day14/*` 演示与 Sprint 1 回顾脚本
- [x] Day 14 单元测试与全套课件

## 上下文链

```
Day 12 LLMClient.complete → Day 13 ResilientLLMClient → Day 14 ChatAssistant 多轮对话 ← 今日
Day 14 messages 历史累积 → Day 15 Token 计数与成本意识
Day 16 流式输出将引入异步 SSE
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | CLI 助手详解 | 深度专题 |
| 12-14 | 练习册 / 状态管理 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | 多轮对话讲义 / Sprint1 总结 / 评审标准 / 精读 / Lab | 阶段收官 |

## 关键设计决策

1. **单一职责**：`ChatAssistant` 编排对话；`MessageHistory` 管历史；`ResilientLLMClient` 管调用  
2. **命令与对话分离**：`is_command` + `handle_command` 拦截斜杠命令，不进入 LLM  
3. **双运行模式**：`run_interactive` 给人用；`run_scripted` 给 pytest 与 CI  
4. **退出自动保存**：`run_interactive` 结束时 `save_history()`，会话可恢复  
5. **错误友好展示**：`ConfigError` / `APIError` 在 `_process_line` 层捕获，不崩溃主循环

## Day 15 预告

明日进入 **Token 计数器**：统计 `usage.prompt_tokens` / `completion_tokens`，建立成本与上下文长度意识，为多轮对话「越聊越长」做量化监控。
