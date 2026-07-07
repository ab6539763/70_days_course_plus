# Day 19 企业案例集：RAG 检索

**编制**：赵岩（产品）+ 陈默（架构）  
**场景**：智链科技金融业务客服与内控

---

## 案例 1：理财产品说明书问答

### 业务背景

用户通过 NexusAgent 询问「稳健增值系列年化收益率多少」，须引用最新说明书，不得编造。

### Day 18 问题

`context_provider` 固定返回 `raw_notice.txt` 前 400 字，用户问客服电话时 context 仍含收益率段落 —— 噪音干扰回答。

### Day 19 方案

```python
rag = RAGContextService.from_sample_docs()
router = IntentRouter(query_context_provider=rag.retrieve_context)
```

`/retrieve 年化收益率` 命中含「8%」片段；`chat_turn` 注入对应 context。

### 效果指标（内测）

| 指标 | Day 18 | Day 19 |
|------|--------|--------|
| context 与 query 相关率（人工抽检） | ~30% | ~85% |
| 「根据文档」类投诉 | 12 条/周 | 预估降至 4 条 |

---

## 案例 2：风险提示合规

### 业务背景

监管要求：涉及「收益」的回复须同屏可见「投资有风险」表述。

### RAG 用法

查询「收益怎么样」时，检索 top_k=3 可同时拉回收益段与风险段（若均在知识库），`retrieve_context` 拼接后 LLM 更易同时引用。

### 运营检查清单

1. `/retrieve 投资有风险` 是否命中  
2. `max_chars` 是否足够容纳双段  
3. Prompt `RAG_QA` 是否要求「须引用风险提示」  

---

## 案例 3：多文档扩展（规划）

### 现状

`sample_docs` 含 `raw_notice.txt` 等，Day 19 已支持 `from_directory`。

### 扩展

```python
service = RAGContextService.from_directory(
    Path("/data/product_docs"),
    pattern="*.txt",
    chunk_size=250,
    overlap=50,
)
```

`RetrievalResult.chunk.source` 标明来源文件，便于审计。

---

## 案例 4：运维调试流程

林晓总结的上线前三步：

```mermaid
flowchart LR
    A[/retrieve 抽测 10 query/] --> B[检查 score 与 source]
    B --> C[/route 确认 rag_qa/]
    C --> D[staging chat_turn 5 轮]
```

周航将此写入 Runbook 草案。

---

## 案例 5：失败与降级

### 场景：知识库未覆盖的新产品

用户问「智链科技区块链 ETF」，检索零命中 → context 为「未检索到相关片段」。

### 产品策略

1. LLM 须在 Prompt 中被告知「无资料时明确说明」  
2. 未来：低分阈值转人工（Day 22+）  
3. 禁止：零命中时编造具体数字  

---

## 案例 6：与竞品对比（课堂讨论）

| 能力 | 通用 ChatGPT 上传文件 | NexusAgent Day 19 |
|------|----------------------|-------------------|
| 知识更新 | 手动上传 | 替换 sample_docs / 目录 |
| 意图联动 | 无 | auto_route + rag_qa |
| 可测性 | 低 | 12 条单测 + /retrieve |
| 语义检索 | 内置 | Day 20 补齐 |

---

## 案例 7：林晓实训日记摘录

> 「下午我用 `/retrieve 内部资料外传` 试了一下，居然也能命中 —— 原来说明书里有保密条款。赵岩说这种 query 应该走 compliance_review，不能仅靠 RAG。这让我理解：**检索解决『找材料』，意图路由解决『干什么』，两层都要对。**」

---

## 讨论题

1. 关键词检索在客服电话精确匹配上的优势？  
2. 何时应增大 `top_k`？何时应减小？  
3. Day 20 向量检索上线后，是否保留 KeywordRetriever 作为混合一路？  

---

## 延伸阅读

- 课件 `23_RAG检索企业实践.md`  
- 课件 `13_深度扩展_Embedding向量检索.md`
