# Day 32 课件索引

**日期**：2026-08-08（星期六）  
**主题**：交叉编码器重排（Cross-Encoder Rerank）— hybrid 宽召回 → top-20 → 精排 → top-3  
**需求**：ZL-NA-REQ-032  
**平台版本**：v0.32.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| Reranker | `rag/reranker.py` | MockCrossEncoder + score_pair |
| RerankConfig | `rag/rerank_config.py` | enabled、candidate_pool、model |
| RerankingRetriever | `rag/reranking_retriever.py` | 两阶段 search 管线 |
| _build_rag_service | `rag/knowledge_store.py` | Hybrid → RerankingRetriever 装配 |
| rerank-config API | `api/knowledge.py` | GET/PUT 精排策略 |
| 演示 | `day32/rerank_demo.py` | 关闭/开启精排对比 |
| API 演示 | `day32/rerank_api_demo.py` | TestClient 端到端 |
| 测试 | `tests/day32/` | 18 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day32/rerank_demo.py
python3 src/day32/rerank_api_demo.py
python3 -m pytest tests/day32/ -v
```

## 关键流程

Day 31 混合检索让正确答案**进候选** → Day 32 **排第一**：`RerankingRetriever` 先让内层 `HybridRetriever` 宽召回 `candidate_pool=20`，再 `MockCrossEncoderReranker` 逐对打分截断 `top_k=3`。

## 核心难点（必读）

**Bi-encoder vs Cross-encoder**：Day 29 向量检索把 query 与 chunk **分别**编码再算相似度，快但交互弱；交叉编码器把 `(query, chunk)` **一起**编码（本课用 `score_pair` mock），慢但细粒度，故只对 top-N 候选运行。

## 设计决策

1. `RerankConfig` 默认 `enabled=True`, `candidate_pool=20`, `model=mock`  
2. `enabled=False` 时 `RerankingRetriever` 完全委托内层 hybrid  
3. `pool = max(candidate_pool, top_k)` 保证精排输入不少于输出  
4. 配置持久化在 `store.json` 的 `rerank_config` 字段  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_交叉编码器重排详解 | 两阶段检索专题 |
| 22_reranker精读 | 源码 + 行级注释 |
| 26_实操Lab手册 | Lab 0–7 含 hit@1 对比 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
PYTHONPATH=src pytest tests/day32/ -q
```

通过标准：`test_phone_query_rerank` 绿；`PUT rerank-config` 关闭后 chat 仍 200。

---

## 两阶段检索直觉（课程核心）

| 阶段 | 组件 | 输入规模 | 输出 | 延迟特征 |
|------|------|----------|------|----------|
| 召回 | HybridRetriever | 全库 | top-20 | 毫秒级 |
| 精排 | MockCrossEncoder | 20 对 | top-3 | 线性于 N |

详见 `11_交叉编码器重排详解.md` 与 `22_reranker精读.md`。

---

## 配套代码路径

| 类型 | 路径 |
|------|------|
| 核心逻辑 | `src/rag/reranker.py` |
| 管线 | `src/rag/reranking_retriever.py` |
| 配置 | `src/rag/rerank_config.py` |
| 装配 | `src/rag/knowledge_store.py` `_build_rag_service` |
| 演示 | `src/day32/rerank_demo.py` |
| 测试 | `tests/day32/`（18 项） |

---

## 常见问题（课前）

**Q 为何不对全库 rerank？**  交叉编码器逐对打分，复杂度 O(N)；只对 hybrid 召回的 20 条可换 hit@1 且控延迟。  
**Q mock 与真实 BGE-reranker 差别？**  接口一致；mock 用 token 覆盖 + bigram 模拟交互，便于 CI 无 GPU。  
**Q 与 Day31 关系？**  正交叠加：Day31 管 hybrid 融合，Day32 在 hybrid 外包一层精排。  

---

## 一周复习计划

| 天 | 内容 |
|----|------|
| D0 | 11 专题 + 22 精读 |
| D1 | Lab 3 开关精排对比 |
| D2 | pytest day32 |
| D3 | 作业 A |
| D4 | 口述 score_pair 公式 |
| D5 | Day33 预习 query rewrite |

---

## 发版检查（Release Captain）

- [ ] PLATFORM_VERSION 0.32.0  
- [ ] tests day31+day32 绿  
- [ ] 课件 30 篇 regenerate  
- [ ] 产品话术 FR-006 已同步客服  
- [ ] rerank-config 默认值已文档化  

---

## 相关仓库路径速查

```
nexus-agent-platform/src/rag/reranker.py
nexus-agent-platform/src/rag/reranking_retriever.py
nexus-agent-platform/src/rag/rerank_config.py
nexus-agent-platform/src/rag/knowledge_store.py   # _build_rag_service
nexus-agent-platform/src/api/knowledge.py         # rerank-config
nexus-agent-platform/src/day32/rerank_demo.py
nexus-agent-platform/tests/day32/
```

---

## 学员画像（完成后）

你将能够：解释两阶段检索；配置 `candidate_pool`；向运营说明「为何 top-1 在开启 rerank 后变化」；编写 `score_pair` 单测；在 incident 时判断该关 rerank 还是缩池。

---

## 每日一句（Day32）

「召回要宽，精排要尖；交叉编码器只看前二十，却把第一答准。」

---

## 课件生成命令

```bash
python3 scripts/course_days/day32.py
```

输出目录：`course/day32/`，30 文件，≥100000 字符校验。

---

## 与其他 Day 链接

- 复习 Day31：`course/day31/27_Day32预习.md`  
- 预习 Day33：`course/day32/27_Day33预习.md`  

**Gold Standard**：本日课件由 `scripts/course_days/day32.py` 生成，遵循与 Day31 相同之 `course_builder` 契约（`read_repo` / `fenced` / `write_course`）。

---

## 版本历史

| 版本 | 说明 |
|------|------|
| v0.32.0-draft | 仅 MockCrossEncoder |
| v0.32.0 | rerank-config API + RerankingRetriever 装配 |

---

## 教研备注

Day32 课件与 Day31 同样经 `course_builder` 重复率校验；`22_reranker精读.md` 为当日最长单篇，建议分配 2 学时精读。
