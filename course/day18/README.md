# Day 18 课件索引

**日期**：2026-07-23（星期四）  
**主题**：Prompt 进阶 — 意图分类器  
**需求**：ZL-NA-REQ-018  
**里程碑**：Phase 2 / Sprint 3 第四日（Day 15–24）

## Sprint 3 进度

昨日完成 Prompt 模板库，今日在「选哪个模板」之前加一层**意图路由**：

- Day 15 Token 计数 → Day 16 流式输出 → Day 17 Prompt 模板与注册表 → **Day 18 意图分类器**
- Day 19+ RAG 检索增强、向量填充 `context`……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# 规则意图分类演示
python3 src/day18/intent_demos.py

# IntentRouter 变量构建演示
python3 src/day18/router_demos.py

# 意图路由 + ChatAssistant 自动选模板
NEXUS_LLM_MOCK=1 python3 src/day18/routed_assistant_demo.py

# 单元测试（12 项）
python3 -m pytest tests/day18/test_intent.py -v
```

## 今日交付物

- [x] `prompts/intent.py` — `IntentMatch`、`RuleBasedIntentClassifier`、`IntentRouter`、`DEFAULT_KEYWORD_RULES`、`INTENT_TEMPLATE_MAP`
- [x] `chat/cli_assistant.py` — `/route` 命令、`auto_route`、`intent_router`
- [x] `src/day18/intent_demos.py`、`router_demos.py`、`routed_assistant_demo.py`
- [x] `tests/day18/test_intent.py`（12 tests）
- [x] Day 18 全套课件（29 篇 + 本 README）

## 上下文链

```
Day 17 PromptTemplate + apply_template → Day 18 意图分类选模板
Day 17 /template 手动切换 → Day 18 /route 预览 + auto_route 自动切换
Day 17 RAG_QA.context → Day 18 IntentRouter.build_variables 注入 context_provider
Day 18 规则分类 MVP → Day 19+ LLM 意图分类（预习）
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | 意图分类详解 | 深度专题 |
| 12-14 | 练习册 / LLM 扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day17 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | 意图路由讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **规则优先 MVP**：关键词打分 + `INTENT_PRIORITY` 同分决胜，零 LLM 成本、可单测  
2. **dataclass 结果**：`IntentMatch` 携带 intent、template_name、confidence、matched_keywords  
3. **路由与模板解耦**：`INTENT_TEMPLATE_MAP` 意图名 → 注册表模板名，可独立演进  
4. **变量构建集中**：`IntentRouter.build_variables` 按模板名注入 `context`、`document`、`text` 等  
5. **Chat 双模式**：`/route` 仅预览分类；`auto_route=True` 在 `chat_turn` 前自动 `route_and_apply`

## Day 19 预告

明日引入 **RAG 检索管线**：`context_provider` 从 `doc_reader` 升级为向量检索，意图 `rag_qa` 的上下文将来自真实知识库。
