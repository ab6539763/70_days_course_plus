# Day 21 Sprint 3 周测题库（教师版）

共 10 题，与 `sprint3_quiz.py` 的 `QUESTIONS` 同步。可用于课堂纸质测验。

**日期**：2026-07-26  
**覆盖范围**：Day 15–20 + Day 21 整合概念  
**及格线**：60 分（`QUIZ_PASS_SCORE`）

---

## 单选题（每题 10 分）

**1.** Token 是大模型计费与上下文窗口的基本计量单位，中文粗略估算约几个字 1 token？  
A. 1 字  B. **1.5-2 字**  C. 5 字  D. 10 字

**解析**：中文约 1.5-2 字 / token，具体因分词器而异。对应 Day 15 `TokenCounter`。

---

**2.** SSE 流式响应中，每条 data 行的典型格式是？  
A. **data: {json}**  B. event: stream  C. chunk: text  D. body: raw

**解析**：Server-Sent Events 使用 `data:` 前缀承载 JSON 块。对应 Day 16 `streaming`。

---

**3.** PromptTemplate.render 缺少必填变量时会抛出？  
A. ValueError  B. **ConfigError**  C. APIError  D. KeyError

**解析**：项目统一用 `ConfigError` 表示配置/模板变量缺失。对应 Day 17 `prompts`。

---

**4.** IntentRouter 为 rag_qa 按用户问题检索上下文应使用？  
A. context_provider  B. **query_context_provider**  C. default_registry  D. auto_route

**解析**：`query_context_provider(query)` 支持按查询动态检索。对应 Day 18-19。

---

**5.** 文档分块 overlap 参数的主要作用是？  
A. 压缩文件  B. **避免语义在块边界断裂**  C. 加密  D. 去重

**解析**：重叠窗口减少关键信息被切在两块之间导致检索丢失。对应 Day 19 `chunker`。

---

**6.** 相对 KeywordRetriever，EmbeddingRetriever 的主要优势是？  
A. 更快  B. **同义表达语义召回**  C. 无需索引  D. 可解释性更高

**解析**：向量余弦相似度能匹配「投资回报率」与「年化收益」等同义表述。对应 Day 20。

---

**7.** cosine_similarity 对非零向量取值范围约为？  
A. 0 到 1  B. **-1 到 1**  C. 0 到 100  D. 任意实数

**解析**：余弦相似度理论范围 [-1, 1]，文本向量多为非负故常见 [0, 1]。对应 Day 20 `vector.py`。

---

**8.** ChatAssistant 的 /similar 命令调用的是？  
A. KeywordRetriever  B. **SimilarQuestionMatcher**  C. IntentRouter  D. StreamingLLMClient

**解析**：`/similar` 预览 FAQ 相似问题匹配结果。对应 Day 20。

---

**9.** RAGContextService.from_sample_docs(use_embedding=True) 注入的检索器是？  
A. KeywordRetriever  B. **EmbeddingRetriever**  C. doc_reader  D. PromptRegistry

**解析**：`use_embedding=True` 切换为 EmbeddingRetriever。对应 Day 20 `context.py`。

---

**10.** Day 21 Sprint 3 周测整合的核心能力是？  
A. 仅多轮对话  B. **FAQ+RAG+意图+工具编排**  C. 仅向量库  D. Docker 部署

**解析**：Day 21 将 Day 15-20 能力通过 ChatOrchestrator 与 ToolRegistry 串联。

---

## 附加问答题（备讲）

**11.** 写出 `build_nexus_tools` 注册的四工具名称。  
**答**：`faq_lookup`、`rag_search`、`intent_classify`、`estimate_tokens`

**12.** `ChatOrchestrator.handle_message` 在调 LLM 之前优先尝试什么？  
**答**：FAQ 高置信直答（`match.score >= faq_direct_threshold`）

**13.** `/tool list` 与 `ToolExecutor.list_help` 的关系？  
**答**：`/tool list` 内部调用 `tool_executor.list_help()` 返回已注册工具摘要

**14.** `tests/day21/test_sprint3.py` 共有多少条测试？  
**答**：12 条

---

## 评分标准

| 分数段 | 建议 |
|--------|------|
| 90-100 | 优秀，直接进入下午工具编排 Lab |
| 60-89 | 及格，薄弱点对照 Day 15-20 笔记 |
| <60 | 重修 Day 15-20，晚自习补测 |

---

## 阅卷注意事项

1. 第 3 题易与 Python 内置 `KeyError` 混淆，以项目 `ConfigError` 为准  
2. 第 4 题需强调 `query` 动态检索 vs 静态 `context_provider`  
3. 第 10 题为综合题，可结合白板画编排流程图加分  
4. 上机复核：`python3 src/day21/sprint3_quiz.py --scripted` 应输出 100/100（验证脚本本身）

---

*程序版：`python3 src/day21/sprint3_quiz.py`*  
*CI 版：`python3 src/day21/sprint3_quiz.py --scripted`*

---

# 附录 A：Sprint 3 周测知识点精讲（Day 15–20 复习专题）

**用途**：周测不及格学员重修读本 | 讲师备课扩展

## 第一讲：Token 与计费（Day 15）

Token 是大语言模型处理文本的最小单位。英文常按词或子词切分；中文因 Unicode 与分词器不同，**粗略按 1.5–2 个汉字估算 1 token**。智链科技内训使用 `TokenCounter.estimate_text` 做离线近似，不调用外部分词 API，保证 CI 稳定。林晓在 Day 15 笔记中写道：「不能把 Token 当字符数，也不能当单词数——它是模型词表里的编号序列长度。」计费账单上的 prompt_tokens、completion_tokens 均由此而来。上下文窗口限制（如 32K、128K）同样以 token 计。Day 21 将 Token 能力封装为 `estimate_tokens` 工具，运营可用 `/tool estimate_tokens 一段很长的合规声明` 在发 LLM 前预估成本。周测第 1 题错选「1 字」的学员往往混淆个别模型现象与课程统一口径，讲义明确：**考试以 1.5–2 字为准**。

## 第二讲：流式输出 SSE（Day 16）

用户等待整段 JSON 回复时感知延迟高。Server-Sent Events（SSE）允许服务端逐块推送生成内容。典型 HTTP 响应头含 `Content-Type: text/event-stream`。每条事件常写作 `data: {"choices":[...]}` 形式。周测第 2 题考查 `data:` 前缀。Day 16 `streaming.py` 演示了 mock 流式拼接；Day 21 编排器暂不封装流式，留待 Day 23 API 层。`handle_message` 当前返回完整 `str`；Day 24 网页版可改为 FAQ 直答一次性返回、LLM 路径走 SSE。

## 第三讲：Prompt 模板与 ConfigError（Day 17）

模板字符串含 `{variable}` 占位符。render 时若缺少 required 变量，项目抛 **ConfigError** 而非 Python 内置 KeyError。周测第 3 题许多学员错选 ValueError 或 KeyError。陈默强调：**背项目约定比背 Python 通用异常更重要**。Day 18 IntentRouter 根据意图选不同 PromptTemplate；工具 `intent_classify` 仅预览意图，不执行 render。

## 第四讲：意图与 query_context_provider（Day 18–19）

`context_provider()` 无参返回静态 context；`query_context_provider(query)` 按**当前用户问题**动态检索。rag_qa 意图必须用后者，否则 RAG 退化为「永远注入同一段文档」。周测第 4 题错选 `context_provider` 的学员约占讲评时 30%。`intent_classify` 工具返回 `IntentRouter.classify(text).summary()`，合规审阅类问句应路由到 compliance 模板。

## 第五讲：RAG 分块 overlap（Day 19）

固定长度分块时，关键句可能被切成两半落在相邻块。overlap 使相邻块共享文字，提高边界召回。周测第 5 题正确答「避免语义在块边界断裂」。`rag_search` 工具内部 `retrieve_context` 已含分块检索全流程，学员无需在工具层指定 overlap。

## 第六讲：Embedding vs 关键词（Day 20）

KeywordRetriever 基于 token 重叠；EmbeddingRetriever 用 TF-IDF 向量 + 余弦相似度，配合 `synonyms.py` 扩展。周测第 6、7、9 题分别考查同义召回、cosine 范围 [-1,1]、`use_embedding=True` 注入 EmbeddingRetriever。建议错题学员重跑 `vector_search_demos.py`。

## 第七讲：FAQ 与 /similar（Day 20）

SimilarQuestionMatcher 对标准 FAQ 库做相似匹配，低于 threshold 返回 None。`/similar` 命令预览匹配，不调 LLM。Day 21 增加 `faq_lookup` 工具与编排器 FAQ 直答两条路径。

## 第八讲：Day 21 整合（周测第 10 题）

正确答案是 **FAQ+RAG+意图+工具编排**。ChatOrchestrator 统一 `handle_message`；ToolRegistry 供显式调试与未来 LLM function calling。林晓总结：「周测第十题是路线图题。」

## 第九讲：模拟加试题

`QUIZ_PASS_SCORE` 默认 60；`test_sprint3.py` 共 12 条；四工具为 faq_lookup、rag_search、intent_classify、estimate_tokens；FAQ 直答默认阈值 0.65；Day 22 主题为前端速成静态聊天页。

## 第十讲：七日知识结构

Day 15 成本意识 → Day 16 体验意识 → Day 17–18 控制生成路径 → Day 19–20 知识落地 → Day 21 工程化编排。缺任何一环，整合 demo 都无法解释。讲师可用作周测不及格学员两小时重修大纲。

## 附录：错题本模板

重修学员须提交：题号、我的答案、正确答案、对应讲义章节、对应源码文件、巩固命令。智链科技培训组要求提交后方可参加晚自习补测。
