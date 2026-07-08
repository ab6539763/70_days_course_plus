# Day 17 课件索引

**日期**：2026-07-22（星期三）  
**主题**：Prompt 基础 — Prompt 模板库  
**需求**：ZL-NA-REQ-017  
**里程碑**：Phase 2 / Sprint 3 第三日（Day 15–24）

## Sprint 3 进度

昨日完成流式输出，今日从「怎么说」入手，把 system 提示词工程化：

- Day 15 Token 计数 → Day 16 流式输出 → **Day 17 Prompt 模板与注册表**
- Day 18 意图分类器（预习）
- Day 19+ RAG 检索增强……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# PromptTemplate 渲染演示
python3 src/day17/prompt_demos.py

# 注册表与文件模板加载
python3 src/day17/registry_demos.py

# RAG Prompt + doc_reader 联调
NEXUS_LLM_MOCK=1 python3 src/day17/rag_prompt_demo.py

# ChatAssistant /template 命令
NEXUS_LLM_MOCK=1 python3 src/day17/assistant_prompt_demo.py

# 单元测试
python3 -m pytest tests/day17/ -v
```

## 今日交付物

- [x] `prompts/base.py` — `PromptTemplate`、`render`、`to_system_message`、`preview`
- [x] `prompts/library.py` — `DEFAULT_ASSISTANT`、`RAG_QA`、`DOC_SUMMARY`、`PRODUCT_FAQ`、`COMPLIANCE_REVIEW`
- [x] `prompts/registry.py` — `PromptRegistry`、`load_from_file`、`default_registry`
- [x] `prompts/templates/customer_service.txt` — 文件扩展模板
- [x] `chat/cli_assistant.py` — `/template` 命令、`apply_template`
- [x] `src/day17/*` 演示脚本
- [x] `tests/day17/test_prompts.py`
- [x] Day 17 全套课件（29 篇）

## 上下文链

```
Day 2 f-string 变量插值 → Day 17 PromptTemplate.render
Day 12 LLMClient.complete → system + user messages
Day 16 流式输出 → 与 Prompt 输入正交（管怎么说 vs 怎么显示）
Day 17 Prompt 模板 → Day 18 意图分类 / Day 28 RAG 上下文拼接
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | FAQ | 排错 |
| 11 | Prompt 模板详解 | 深度专题 |
| 12-14 | 练习册 / 少样本扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day2 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | Prompt 工程讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |

## 关键设计决策

1. **标准库优先**：`str.format` 风格 `{variable}`，与 Day 2 f-string 一脉相承  
2. **dataclass 建模**：`PromptTemplate` 不可变语义 + `__post_init__` 自动推断 `required_vars`  
3. **注册表模式**：内置 `library.py` + 文件 `templates/*.txt` 热加载  
4. **与 Chat 集成**：`to_system_message` 直接产出 `ChatMessage("system", ...)`  
5. **安全预览**：`preview()` 用 `<var>` 占位，便于 RAG 上下文长度估算

## Day 18 预告

明日引入 **意图分类器**：在模板切换之前，先判断用户想走「问答 / 摘要 / 合规审阅」哪条链路，为 Agent 路由打基础。
