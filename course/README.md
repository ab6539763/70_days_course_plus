# 70天培训课程 — 课程总览

## 培训基本信息

| 项目 | 说明 |
|------|------|
| **培训周期** | 70 天（10 周），每天约 6-8 小时 |
| **授课形式** | 上午理论 + 下午实操 + 晚自习答疑 |
| **目标学员** | 零编程基础或少量基础的转行者、在校生、产品经理 |
| **培养目标** | 独立开发 RAG、Agent 应用，微调小模型并部署上线 |
| **最终产出** | NexusAgent 企业级智能体平台（完整可部署） |

## 每日课件结构（统一模板）

每一天的 `course/dayXX/` 目录包含以下标准文件：

| 文件 | 内容 |
|------|------|
| `00_旁白解读.md` | 以第三人称旁白串联上下文，解释「为什么学这个」「和项目什么关系」 |
| `01_企业背景与今日任务.md` | 当日 Sprint 背景、站会纪要、任务分配 |
| `02_需求文档.md` | 当日功能需求（PRD 节选）、验收标准、接口定义 |
| `03_架构设计.md` | 架构图、模块划分、技术选型说明 |
| `04_流程图与示意图.md` | Mermaid 流程图、时序图、状态图 |
| `05_课堂笔记_上午.md` | 上午课程完整笔记 |
| `06_课堂笔记_下午.md` | 下午实操完整笔记 |
| `07_晚自习.md` | 晚自习内容（如有） |
| `08_作业.md` | 课后作业（含难度分级） |
| `09_作业答案.md` | 作业参考答案与讲解 |
| `code/` | 当日配套代码（带详细注释） |

## 企业级项目迭代主线

整个 70 天，所有学习都围绕 **NexusAgent 灵犀智能体平台** 展开：

```
Day 1-7    → 项目立项、开发环境、CLI 工具原型
Day 8-14   → 面向对象重构、首次 LLM API 调用
Day 15-21  → Prompt 工程、Function Calling
Day 22-24  → FastAPI 后端、网页聊天界面
Day 25-31  → 文档处理、向量库、基础 RAG
Day 32-38  → 高级 RAG、Rerank、企业知识库项目
Day 39-45  → ReAct Agent、LangGraph、MCP
Day 46-50  → 多 Agent 办公助手项目
Day 51-57  → LoRA 微调、Docker 部署
Day 58-70  → 毕业设计、平台全功能上线
```

## 考核方式

- **每周小测**：Day 7、14、21、31、38、45、50、57
- **阶段项目**：Day 14（CLI 对话助手）、Day 37-38（知识库系统）、Day 48-50（多 Agent 助手）
- **毕业设计**：Day 58-65（完整平台或垂直领域应用）

## 学习建议

1. **严格按天学习**：每天的课件环环相扣，跳天学习会导致上下文断裂
2. **先读旁白**：`00_旁白解读.md` 会告诉你今天的代码在整个平台中的位置
3. **代码必须手写**：不要复制粘贴，打字过程就是理解过程
4. **每日 Git 提交**：commit message 参照团队规范（见 `team/GIT_CONVENTION.md`）
5. **遇到问题先查需求文档**：企业开发中，需求文档是最高优先级

## 当前进度

课件 Day 24–38 由 `scripts/course_days/dayXX.py` 生成，质量标准对齐 Day 23（每篇独立内容、≥10 万字/期）。一键重生成：

```bash
python3 scripts/regenerate_courses_day24_30.py
```

全链路交付门禁（课件审计 + day01–38 E2E + Sprint3 冒烟）：

```bash
bash scripts/delivery_check.sh
```

- [x] Day 1-5
- [x] Day 6：函数、作用域、lambda、递归；`src/utils/` 工具库与 `todo_manager_v3` 重构
- [x] Day 7：第一周复习、通讯录管理系统、周测（Sprint 1 收官）
- [x] Day 8：面向对象（上）、ChatMessage 类与 MessageHistory
- [x] Day 9：面向对象（下）、BaseModel 抽象类体系与 ModelConfig
- [x] Day 10：模块与异常、core/services 包结构重组
- [x] Day 11：文件与标准库、doc_reader 批量读取
- [x] Day 12：网络与 API、llm/client 首次 LLM 调用
- [x] Day 13：装饰器与异步、llm/retry API 重试与超时
- [x] Day 14：阶段项目一、cli_assistant 多轮对话助手
- [x] Day 15：大模型原理科普、Token 计算器
- [x] Day 16：API 参数详解、llm/streaming 流式输出
- [x] Day 17：Prompt 基础、prompts 模板库
- [x] Day 18：Prompt 进阶、意图分类器与自动路由
- [x] Day 19：RAG 检索入门、文档分块与关键词检索
- [x] Day 20：Embedding 向量相似度与相似问题匹配
- [x] Day 21：Sprint 3 周测、工具调用整合与编排器
- [x] Day 22：前端速成、静态聊天页面 frontend/
- [x] Day 23：FastAPI Chat REST API、/api/chat 与前端对接
- [x] Day 24：Sprint 3 收官、网页版 ChatGPT 克隆完整整合
- [x] Day 25：Phase 3 启动、企业知识库 ingestion 与上传 API
- [x] Day 26：文档解析增强（Markdown / PDF）与分块策略对比
- [x] Day 27：分块参数调优与检索质量 A/B 评估
- [x] Day 28：知识库全量重建（rebuild）
- [x] Day 29：Chroma 向量库持久化（替换 JSON 向量索引）
- [x] Day 30：增量索引（upload 增量 upsert Chroma）
- [x] Day 31：混合检索（关键词 + 向量融合）
- [x] Day 32：交叉编码器重排（Rerank — hybrid top-20 → 精排 top-3）
- [x] Day 33：查询改写（Query Rewrite — 口语问句规范化）
- [x] Day 34：引用溯源（Citation Traceability — chat citations[] + 可解释 RAG）
- [x] Day 35：多查询扩展（HyDE / Query Expansion — 宽召回 + merge 去重）
- [x] Day 36：自适应路由（Query Router — 按意图动态 expand/rewrite）
- [x] Day 37：Self-RAG 答案校验（Answer Validation — 生成后 citations 一致性校验）
- [x] Day 38：多轮 Self-RAG 校验重试（Validation Retry — 失败后 rag_wide 重检索）
- [ ] Day 39-70：持续更新中
