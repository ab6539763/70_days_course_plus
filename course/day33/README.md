# Day 33 课件索引

**日期**：2026-08-09（星期日）  
**主题**：查询改写（Query Rewrite）— 口语问句 → 规则改写 → hybrid → rerank  
**需求**：ZL-NA-REQ-033  
**平台版本**：v0.33.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| QueryRewriter | `rag/query_rewriter.py` | RuleBasedQueryRewriter + DEFAULT_RULES |
| RewriteConfig | `rag/rewrite_config.py` | enabled、mode、fallback、max_rewrite_len |
| RewritingRetriever | `rag/rewriting_retriever.py` | 改写后委托 inner 检索 |
| _build_rag_service | `rag/knowledge_store.py` | RewritingRetriever 最外层装配 |
| rewrite-config API | `api/knowledge.py` | GET/PUT + rewrite-preview |
| 演示 | `day33/rewrite_demo.py` | 关闭/开启改写对比 |
| API 演示 | `day33/rewrite_api_demo.py` | TestClient 端到端 |
| 测试 | `tests/day33/` | 20 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day33/rewrite_demo.py
python3 src/day33/rewrite_api_demo.py
python3 -m pytest tests/day33/ -v
```

## 关键流程

Day 32 rerank 让正确答案**排第一** → Day 33 让用户**问对问题**：`RewritingRetriever` 先用 `RuleBasedQueryRewriter` 把「那个理财能赚多少」规范为「年化收益率是多少」，再进入 hybrid → rerank 管线。

## 核心难点（必读）

**改写 vs 生成**：改写只规范化检索 query，不回答用户；须 `rewrite-preview` 审计 rule_id，避免越权扩写。

## 设计决策

1. `RewriteConfig` 默认 `enabled=True`, `mode=rules`  
2. `enabled=False` 时直通 inner，零改写开销  
3. `fallback_to_original=True` 防止空改写  
4. 配置持久化在 `store.json` 的 `rewrite_config` 字段  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_查询改写详解 | 规则表与审计专题 |
| 22_query_rewriter精读 | 源码 + 行级注释 |
| 26_实操Lab手册 | Lab 0–7 含口语问句对比 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day33/rewrite_api_demo.py
PYTHONPATH=src pytest tests/day33/ -q
```

通过标准：`test_rule_rewrite_colloquial_yield` 绿；`POST rewrite-preview` 返回含「年化」。

---

## 三阶段 RAG 直觉

| 阶段 | 组件 | 作用 |
|------|------|------|
| 改写 | RuleBasedQueryRewriter | 口语 → 检索 query |
| 召回+融合 | HybridRetriever | 宽召回 |
| 精排 | RerankingRetriever | top-N 尖排 |

详见 `11_查询改写详解.md` 与 `22_query_rewriter精读.md`。

---

## 配套代码路径

| 类型 | 路径 |
|------|------|
| 核心逻辑 | `src/rag/query_rewriter.py` |
| 管线 | `src/rag/rewriting_retriever.py` |
| 配置 | `src/rag/rewrite_config.py` |
| 装配 | `src/rag/knowledge_store.py` `_build_rag_service` |
| 演示 | `src/day33/rewrite_demo.py` |
| 测试 | `tests/day33/`（20 项） |

---

## 常见问题（课前）

**Q rewrite 与 rerank 谁先？**  先 rewrite 再检索；rerank 在 inner 管线内。  
**Q 为何用规则不用 LLM？**  可审计、无 GPU、CI 稳定；接口预留扩展。  
**Q 与 Day32 关系？**  串联：Day33 外包层，Day32 仍在 inner。

---

## 发版检查

- [ ] PLATFORM_VERSION 0.33.0  
- [ ] tests day32+day33 绿  
- [ ] 课件 30 篇 regenerate  

---

## 课件生成命令

```bash
python3 scripts/course_days/day33.py
```

输出目录：`course/day33/`，30 文件，≥100000 字符校验。

---

## 版本历史

| 版本 | 说明 |
|------|------|
| v0.33.0-draft | 仅 rules 模式 |
| v0.33.0 | rewrite-config API + rewrite-preview |
