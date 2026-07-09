# Day 21 课件索引

**日期**：2026-07-26（星期日）  
**主题**：Sprint 3 周测 / 工具调用整合  
**需求**：ZL-NA-REQ-021  
**里程碑**：Phase 2 / Sprint 3 第七日（Day 15–24）

## Sprint 3 进度

昨日完成 Embedding 向量检索与 FAQ 匹配，今日进行 **Sprint 3 周测**，并将 Day 15–20 能力通过 `ToolRegistry`、`ToolExecutor` 与 `ChatOrchestrator` 整合为统一编排链路。

- Day 15 Token 计数 → Day 16 流式输出 → Day 17 Prompt 模板 → Day 18 意图分类 → Day 19 RAG 关键词 → Day 20 Embedding → **Day 21 周测 + 工具编排**
- Day 22 前端速成 / 静态聊天页面……

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src

# Sprint 3 周测（10 题 Day 15-20）
python3 src/day21/sprint3_quiz.py
python3 src/day21/sprint3_quiz.py --scripted

# 能力里程碑回顾
python3 src/day21/sprint3_review.py

# 工具注册与执行演示
python3 src/day21/tool_demos.py

# FAQ 直答 + 编排 + /tool 联调
NEXUS_LLM_MOCK=1 python3 src/day21/integrated_assistant_demo.py

# 单元测试（12 项）
python3 -m pytest tests/day21/test_sprint3.py -v
```

## 今日交付物

- [x] `src/tools/tool_registry.py` — `ToolDefinition`、`ToolRegistry`、`build_nexus_tools`
- [x] `src/tools/executor.py` — `ToolExecutor`
- [x] `src/chat/orchestrator.py` — `ChatOrchestrator`、`OrchestratorConfig`
- [x] `src/chat/cli_assistant.py` — `/tool` 命令扩展
- [x] `src/day21/sprint3_quiz.py`、`sprint3_review.py`、`tool_demos.py`、`integrated_assistant_demo.py`
- [x] `tests/day21/test_sprint3.py`（12 tests）
- [x] Day 21 全套课件（29 篇 + 本 README）

## 上下文链

```
Day 20 Embedding + /similar → Day 21 工具化 faq_lookup / rag_search
Day 18 IntentRouter → Day 21 intent_classify 工具
Day 15 TokenCounter → Day 21 estimate_tokens 工具
Day 14 ChatAssistant → Day 21 ChatOrchestrator 编排 FAQ 直答 + auto_route
Day 21 CLI 整合 → Day 22 静态聊天页面 frontend/
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 00 | [旁白解读](00_旁白解读.md) | Sprint 3 周测故事线与学习路径 |
| 01-04 | 背景 / 需求 / 架构 / 流程图 | 企业情境与设计 |
| 05-07 | 课堂笔记 / 晚自习 | 当日节奏 |
| 08-09 | 作业与答案 | 课后巩固 |
| 10 | [Sprint3周测题库](10_Sprint3周测题库.md) | 教师版周测试卷 |
| 11 | 工具调用整合详解 | 深度专题 |
| 12-14 | 练习册 / Function Calling 扩展 / 企业案例 | 扩展阅读 |
| 15-21 | 实录 / 卡片 / 速查 / Day20 对照 / 补充 / 走查 / 竞赛 | 讲师与学生工具 |
| 22-26 | Orchestrator 讲义 / 企业实践 / Sprint3 回顾 / 精读 / Lab | Phase 2 纵深 |
| 27 | [Day22 预习](27_Day22前端速成预习.md) | 明日前端速成预告 |

## 关键设计决策

1. **工具即能力封装**：FAQ、RAG、意图、Token 各成独立 `ToolDefinition`，handler 复用已有服务
2. **编排优先 FAQ 直答**：`ChatOrchestrator` 高置信 FAQ 跳过 LLM，降本增效
3. **/tool 显式调试**：`list` 列工具、`faq_lookup` 简写参数，与 `auto_route` 隐式路由互补
4. **周测闭环**：`sprint3_quiz.py` 10 题覆盖 Day 15–20，`test_sprint3.py` 12 条 CI 守护
5. **为 Web 铺路**：编排器接口稳定，Day 22–24 前端与 FastAPI 直接调用 `handle_message`

## Day 22 预告

明日 **前端速成**：在 `frontend/` 搭建静态聊天页面，为 FastAPI Chat REST API 提供浏览器入口。详见 [27_Day22前端速成预习.md](27_Day22前端速成预习.md)。

---

## 本日学习成效自检（智链科技培训组）

完成 Day 21 后，学员应能够：（1）独立运行 `sprint3_quiz.py` 并达到及格线；（2）解释 `ToolDefinition` 四字段含义；（3）使用 `/tool` 调试四内置工具；（4）描述 `ChatOrchestrator.handle_message` 的两步策略；（5）通过 `pytest tests/day21/test_sprint3.py` 全部十二项。若五项中有两项未达成，请重修 10_ 周测题库附录 A 与 26_ Lab 手册。林晓、陈默、赵岩、周航四人组叙事贯穿课件，帮助学员建立团队协作心智。Sprint 3 剩余三日将聚焦浏览器与 API，请保持编排器接口在心中——`handle_message` 是明日之后所有用户界面的共同后端入口。

### 课件统计与使用说明

本目录共三十个文件（二十九篇正文 + 本 README），中文总字数逾三万，配套代码位于 `nexus-agent-platform/src/day21/` 与 `src/tools/`、`src/chat/orchestrator.py`。建议学习路径：晨读 00_ 旁白 → 上午 10_ 周测 → 下午 11_ 详解与 26_ Lab → 晚间 08_ 作业。教师授课使用 10_ 教师版题库、15_ 实录、19_ 补充阅读；学员复习使用 16_ 卡片、17_ 速查、24_ 阶段回顾。所有 mermaid 图可在支持渲染的 Markdown 预览器中查看；若无法渲染，请对照 04_ 流程图文字说明。智链科技培训组祝各位 Day 21 学习顺利，明日见 frontend。

**版权与反馈**：课件内容以仓库最新版为准；发现与代码不一致处请提 Issue 标注 ZL-NA-REQ-021。讲师反馈群每日 20:00 汇总学员疑问，次日晨会由陈默统一答疑。周测成绩、Lab 报告、作业提交截止时间为 Day 22 上午 09:00 课前。未提交者视为缺勤一次。鼓励学员互相 review 作业 B 的 tool 输出，学习彼此调试参数写法。

**Day 21 核心命令再抄一遍**：`export PYTHONPATH=src NEXUS_LLM_MOCK=1`；`python3 src/day21/sprint3_quiz.py --scripted`；`python3 src/day21/tool_demos.py`；`python3 src/day21/integrated_assistant_demo.py`；`python3 -m pytest tests/day21/test_sprint3.py -v`。五条命令全部成功，即达到智链科技内训部定义的「Day 21 机检合格」。文字课件与代码仓库共同构成完整学习闭环，缺一不可。

**致谢**：感谢赵岩产品团队提供 FAQ 与合规场景，感谢周航维护 CI，感谢林晓等学员在内测班反馈 `/tool` 简写需求，感谢陈默架构评审冻结 `handle_message` 接口。Sprint 3 后半程见。

**文档版本**：2026-07-26 v1.0 首发，对应 NexusAgent 平台 Day 21 交付。后续修订将更新 FR 状态与测试条数，请以 Git 提交记录为准。培训部联系人：course@zhilian-tech.example（虚构）。

**最后提醒**：Day 22 前端速成不考 Python，但会考你是否理解消息从浏览器到 `ChatOrchestrator` 的旅程。今晚请读完 27_ 预习文档，准备好 Chrome 或 Firefox 浏览器。周测未及格者务必完成 10_ 附录 A 精讲再睡。祝各位在 Sprint 3 下半场持续进步，在网页版 Chat 交付时收获成就感。

本 README 索引二十九篇正文：从 00_ 旁白到 27_ Day22 预习，覆盖需求、架构、实验、周测、案例与竞赛。按序号通读约需六至八小时；配合实操 Lab 约需一个完整工作日。智链科技 NexusAgent 七十天培训，天天有交付，日日可验证。第二十一日完稿。

> 课件寄语：工具为器，编排为道；周测为镜，整合为桥。桥对面是前端与 API，是用户看得见摸得着的 NexusAgent。林晓加油。陈默赵岩周航同在。全文完。谢谢阅读。再会。安好
