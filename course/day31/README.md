# Day 31 课件索引

**日期**：2026-08-07（星期五）  
**主题**：混合检索（Hybrid Retrieval）— 关键词 + 向量融合  
**需求**：ZL-NA-REQ-031  
**平台版本**：v0.31.0

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| HybridRetriever | `rag/hybrid_retriever.py` | vector / keyword / hybrid 三模式 |
| RetrievalConfig | `rag/retrieval_config.py` | mode、fusion、权重、rrf_k |
| _build_rag_service | `rag/knowledge_store.py` | 装配 HybridRetriever |
| retrieval-config API | `api/knowledge.py` | GET/PUT 检索策略 |
| 演示 | `day31/hybrid_demo.py` | 三模式对比 |
| API 演示 | `day31/hybrid_api_demo.py` | TestClient 端到端 |
| 测试 | `tests/day31/` | 17 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day31/hybrid_demo.py
python3 src/day31/hybrid_api_demo.py
python3 -m pytest tests/day31/ -v
```

## 关键流程

Day 30 增量让库**快更新** → Day 31 **查得准**：稀疏关键词腿补精确 token（SKU、手机号），稠密向量腿补语义问句，RRF 或加权融合两路结果。

## 核心难点（必读）

**分数尺度不一致**：KeywordRetriever 的 TF 分数与向量 cosine 不在同一量纲——故默认 `fusion=weighted` 时先 `_normalize_scores` 再按 `keyword_weight` / `vector_weight` 加权；`fusion=rrf` 则完全忽略原始分数，仅用排名做 Reciprocal Rank Fusion。

## 设计决策

1. `RetrievalConfig` 默认 `mode=hybrid`, `fusion=weighted`, `0.35/0.65`  
2. hybrid 模式候选池 `pool = max(top_k * 4, 8)`  
3. vector / keyword 单模式时 HybridRetriever 直接委托子检索器  
4. 配置持久化在 `store.json` 的 `retrieval_config` 字段  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_混合检索详解 | RRF 与加权专题 |
| 22_hybrid_retriever精读 | 源码 + 行级注释 |
| 26_实操Lab手册 | Lab 0–7 含融合对比 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
PYTHONPATH=src pytest tests/day31/ -q
```

通过标准：`test_exact_phone_keyword_favors_hybrid` 绿；`PUT retrieval-config` 切换 `rrf` 后 chat 200。

---

## 混合检索直觉（课程核心）

| Query 类型 | 向量腿 | 关键词腿 | hybrid 价值 |
|------------|--------|----------|-------------|
| 「年化收益」语义 | 强 | 中 | 稳 |
| 「13900001111」精确 | 弱 | 强 | **显著提升** |
| 「投资有风险吗」口语 | 强 | 中 | RRF 常更稳 |

详见 `11_混合检索详解.md` 与 `22_hybrid_retriever精读.md`。

---

## 配套代码路径

| 类型 | 路径 |
|------|------|
| 核心逻辑 | `src/rag/hybrid_retriever.py` |
| 配置 | `src/rag/retrieval_config.py` |
| 装配 | `src/rag/knowledge_store.py` `_build_rag_service` |
| 演示 | `src/day31/hybrid_demo.py` |
| 测试 | `tests/day31/`（17 项） |

---

## 常见问题（课前）

**Q 为何不用 BM25？**  教学栈用 KeywordRetriever（token 重叠 + TF），接口与融合层一致；BM25 是工程升级项。  
**Q 权重如何调？**  精确查询多 → 提高 keyword_weight；口语多 → 提高 vector_weight；不确定 → 试 RRF。  
**Q 与 Day30 关系？**  正交：增量管写入，混合管读取。  

---

## 一周复习计划

| 天 | 内容 |
|----|------|
| D0 | 11 专题 + 22 精读 |
| D1 | Lab 3 融合对比 |
| D2 | pytest day31 |
| D3 | 作业 A |
| D4 | 口述 RRF 公式 |
| D5 | Day32 预习 rerank |

---

## 发版检查（Release Captain）

- [ ] PLATFORM_VERSION 0.31.0  
- [ ] tests day30+day31 绿  
- [ ] 课件 30 篇 regenerate  
- [ ] 产品话术 FR-005 已同步客服  
- [ ] retrieval-config 默认值已文档化  

---

## 相关仓库路径速查

```
nexus-agent-platform/src/rag/hybrid_retriever.py
nexus-agent-platform/src/rag/retrieval_config.py
nexus-agent-platform/src/rag/knowledge_store.py   # _build_rag_service
nexus-agent-platform/src/api/knowledge.py         # retrieval-config
nexus-agent-platform/src/day31/hybrid_demo.py
nexus-agent-platform/tests/day31/
```

---

## 学员画像（完成后）

你将能够：配置 hybrid/rrf；向运营解释「为何纯向量搜不到手机号」；编写融合单元测试；在 incident 时判断该切 keyword 还是调权重。

---

## 每日一句（Day31）

「增量让知识库呼吸，混合让回答睁眼。」

---

## 课件生成命令

```bash
python3 scripts/course_days/day31.py
```

输出目录：`course/day31/`，30 文件，≥110000 字符校验。

---

## 与其他 Day 链接

- 复习 Day30：`course/day30/27_Day31混合检索预习.md`  
- 预习 Day32：`course/day31/27_Day32预习.md`  

**Gold Standard**：本日课件由 `scripts/course_days/day31.py` 生成，遵循与 Day30 相同之 `course_builder` 契约（`read_repo` / `fenced` / `write_course`）。
