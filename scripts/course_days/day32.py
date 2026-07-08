#!/usr/bin/env python3
"""Gold-standard course material builder for Day 32 — 交叉编码器重排 Rerank."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-032"
VER = "v0.32.0"
REPO = "nexus-agent-platform/src"

RERANKER = read_repo(f"{REPO}/rag/reranker.py")
RERANK_CONFIG = read_repo(f"{REPO}/rag/rerank_config.py")
RERANKING_RETRIEVER = read_repo(f"{REPO}/rag/reranking_retriever.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
KNOWLEDGE_API = read_repo(f"{REPO}/api/knowledge.py")
RERANK_DEMO = read_repo(f"{REPO}/day32/rerank_demo.py")
RERANK_API_DEMO = read_repo(f"{REPO}/day32/rerank_api_demo.py")
TEST_RERANKER = read_repo(f"{REPO}/../tests/day32/test_reranker.py")
TEST_RERANK_API = read_repo(f"{REPO}/../tests/day32/test_rerank_api.py")

_BUILD_RAG = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def _build_rag_service"): KNOWLEDGE_STORE.find(
        "_store: KnowledgeStore"
    )
]
_RERANK_API = KNOWLEDGE_API[
    KNOWLEDGE_API.find('@router.get("/rerank-config"'): KNOWLEDGE_API.find(
        '@router.get("/chunk-config"'
    )
]
_RERANKING_SEARCH = RERANKING_RETRIEVER[
    RERANKING_RETRIEVER.find("def search(self"): RERANKING_RETRIEVER.rfind("]")
    + 1
]
_MOCK_RERANK = RERANKER[
    RERANKER.find("class MockCrossEncoderReranker"): RERANKER.find("def score_pair")
]
_SCORE_PAIR = RERANKER[
    RERANKER.find("def score_pair"): RERANKER.find("def _bigram_overlap")
]
_BIGRAM = RERANKER[RERANKER.find("def _bigram_overlap") :]
_RERANK_CFG_METHODS = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def get_rerank_config"): KNOWLEDGE_STORE.find(
        "def ingest_bytes"
    )
]


def build() -> dict[str, str]:
    files = {
        "README.md": _readme(),
        "00_旁白解读.md": _narration(),
        "01_企业背景与今日任务.md": _file01(),
        "02_需求文档.md": _prd(),
        "02_需求文档_扩展.md": _prd_extended(),
        "03_架构设计.md": _architecture(),
        "04_流程图与示意图.md": _file04(),
        "05_课堂笔记_上午.md": _file05(),
        "06_课堂笔记_下午.md": _file06(),
        "07_晚自习.md": _file07(),
        "08_作业.md": _file08(),
        "09_作业答案.md": _file09(),
        "10_Rerank验收清单.md": _file10(),
        "11_交叉编码器重排详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_两阶段检索方法论.md": _file13(),
        "14_企业案例集_hit_at_1优化.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_Rerank_API速查手册.md": _file17(),
        "18_与Day31能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_reranker精读.md": _file22(),
        "23_候选池与延迟预算实践.md": _file23(),
        "24_Phase3第八日总结.md": _file24(),
        "25_rerank_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day33预习.md": _file27(),
    }
    return files


def _readme() -> str:
    return f"""# Day 32 课件索引

**日期**：2026-08-08（星期六）  
**主题**：交叉编码器重排（Cross-Encoder Rerank）— hybrid 宽召回 → top-20 → 精排 → top-3  
**需求**：{REQ}  
**平台版本**：{VER}

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
"""


def _narration() -> str:
    return f"""# Day 32 旁白解读

2026 年 8 月 8 日，星期六。林晓打开客服质检报表：混合检索上线后，「正确答案进 top-3」率从 61% 升到 78%，但 **hit@1** 仍只有 54%——用户只看第一条引用，第二条等于没答。

赵岩指着白板上的漏斗：

```
全库 ──► hybrid top-20 ──► rerank top-3 ──► LLM
         （宽）              （尖）
```

陈默：「Day 31 让号码进候选；今天让**最相关**的那条 chunk 排到第 1。交叉编码器贵，所以只给前 20 条。」

下午 Lab 第二节，林晓跑 `rerank_demo.py`。同一问句「年化收益率可达」：

- 关闭精排：top-1 落在泛泛的「市场有风险」段落（hybrid 分高但语义飘）  
- 开启精排：top-1 命中「本产品年化收益率可达 8%」（`score_pair` 子串 + token 覆盖胜出）

周航举手：「这和 bi-encoder 向量有啥区别？」陈默在 `(query, chunk)` 外画框：「向量是两人背对背猜像不像；交叉编码器是两人面对面逐字对读。」

第四节，她 `PUT /api/knowledge/rerank-config` 把 `candidate_pool` 从 20 调到 10，延迟降 40%，hit@1 略降——全班填延迟预算表。

```mermaid
journey
    title Day 32
    section 上午
      bi vs cross 白板: 5: 陈默
      score_pair 走读: 4: 林晓
    section 下午
      rerank_demo 对比: 5: 林晓
      API 调 pool: 4: 林晓
      18 tests green: 5: 周航
```

**金句**：陈默：「召回是渔网，精排是挑鱼；网撒多大、挑多细，都是 SLA 题。」

---

## 技术旁白：candidate_pool 为何默认 20

`RerankingRetriever.search` 在 `enabled=True` 时调用 `inner.search(query, top_k=pool)`，`pool=max(candidate_pool, top_k)`。20 是教学库在「漏召回」与「rerank 耗时」间的折中：池太小会丢掉 hybrid 第 15 名处的真答案；太大则 mock 也要跑更多 `score_pair`。

---

## 现场对话（转写节选）

**学员**：能否 candidate_pool=100？  
**陈默**：配置上限 100，但 P95 线性涨；生产要压测。  

**学员**：关 rerank 会影响 chat 吗？  
**陈默**：会，top-3 顺序变；`enabled=False` 时行为等同 Day31 hybrid。

---

## 林晓日记节选

「昨天还在纠结 fusion，今天纠结 pool 多大。原来检索漏斗还有第二截。」

---

## 时间线

| 时刻 | 事件 |
|------|------|
| 09:00 | 复现 hit@1 不足 |
| 10:30 | 讲 RerankConfig |
| 11:00 | **score_pair 白板推导** |
| 14:00 | rerank_demo 双列 |
| 15:00 | API rerank-config |
| 16:30 | 18 tests green |

---

## 媒体稿（公关）

智链 NexusAgent {VER} 上线交叉编码器重排，在保持混合检索宽召回的同时，将 FAQ 首条引用准确率进一步提升，典型金融问句 hit@1 提升可观测。

---

## 幕后：教研组会议纪要

**议题**：默认 pool 20 还是 30？  
**结论**：20 与延迟预算表一致；文档推荐高精度场景试 30。  
**行动**：Day32 课件 Lab4 强制对比 enabled 开关。

---

## 学员反馈（试讲）

「终于理解为什么向量 top-1 不一定是 LLM 该看的 —— rerank 是第二意见。」  
「score_pair 的 length_penalty 很妙，长政策文不再霸榜。」

---

## 彩蛋：电影隐喻

陈默：「hybrid 是海选；cross-encoder 是决赛评委团，只能看 20 位选手。」
"""


def _file01() -> str:
    return f"""# Day 32 企业背景与今日任务

**需求**：{REQ} | **版本**：{VER}

## 背景

质检周报：混合检索后 top-3 含答案率 78%，但 **hit@1 仅 54%**。根因是 hybrid 融合分与「query-chunk 细粒度相关」不完全一致——噪声 chunk（长政策文、泛化风险提示）常因某路高分占据第 1。今日交付 **RerankingRetriever** 与 **rerank-config API**。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | Reranker + score_pair + RerankingRetriever + RerankConfig |
| 下午 | Lab：开关精排对比 + API 调 pool + chat 验证 |
| 晚自习 | 读 Day 33 query rewrite 预习 |

## 自检

- [ ] 理解 bi-encoder 与 cross-encoder 差异  
- [ ] 能解释 `candidate_pool` 与 `top_k` 关系  
- [ ] 读过 `02_需求文档.md` FR-004  

---

## 企业背景详述

智链理财知识库经 Day31 hybrid 后，客服「查电话 / 查收益率」类 query 召回改善，但 LLM 上下文仅取 top-3，**排序**成为新瓶颈。{REQ} 要求可开关、可调池的两阶段检索，默认 mock 交叉编码器便于 CI。

---

## 相关方

| 角色 | 诉求 |
|------|------|
| 客服 | 第一条引用就要对 |
| 产品 | 可开关精排做 A/B |
| 开发 | Reranker 可插拔 |
| 运维 | status 暴露 rerank_config |

---

## 今日代码阅读顺序

1. `rerank_config.py`（15 min）  
2. `reranker.py` score_pair（30 min）  
3. `reranking_retriever.py`（30 min）  
4. `knowledge_store._build_rag_service`（15 min）  
5. `api/knowledge.py` rerank-config（15 min）  
6. `tests/day32/`（30 min）  

---

## 成功画像

17:30 你能向客服主管解释：「为何开启 rerank 后第一条引用更准，以及 pool 变大为何变慢。」
"""


def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：知识库交叉编码器重排  
**优先级**：P0  
**平台版本**：{VER}

---

## 1. 背景

Day 31 混合检索提升召回，但 top-1 精度不足：融合分高的 chunk 未必与 query 最细粒度相关。工业界标准做法是在宽召回后对 top-N 用 **Cross-encoder** 重排。教学栈用 `MockCrossEncoderReranker` 模拟交互打分，接口与真模型一致。

## 2. 目标

- hybrid 召回 `candidate_pool`（默认 20）→ rerank → `top_k`（默认 3）  
- `RerankConfig` 可开关、调池、选模型（现阶段仅 mock）  
- 配置持久化并经 REST 热更新  
- 默认开启 rerank，兼顾 hit@1 与可测性  

## 3. 功能需求

### FR-001 Reranker 抽象与 Mock 实现

- 抽象类 `Reranker.rerank(query, candidates, top_k)`  
- `MockCrossEncoderReranker` 用 `score_pair` 模拟交叉编码  
- 子串命中 → 1.0；否则 coverage + bigram − length_penalty  

### FR-002 RerankingRetriever 两阶段管线

- 持有 `inner`（HybridRetriever）与 `reranker`  
- `enabled=False` → 委托 `inner.search`  
- `enabled=True` → `pool=max(candidate_pool, top_k)` 召回再 rerank  

### FR-003 RerankConfig 与校验

- 字段：`enabled`, `candidate_pool`, `model`  
- `validate()`：pool ∈ [1,100]；model 仅 `mock`  

### FR-004 持久化与 status

- `store.json` 存 `rerank_config`  
- `GET /api/knowledge/status` 含 `rerank_config`  
- `platform_version` 为 `{VER}`  

### FR-005 rerank-config REST API

- `GET /api/knowledge/rerank-config`  
- `PUT /api/knowledge/rerank-config` 更新并 `save()`  
- 非法 body → HTTP 422  

### FR-006 RAG 装配

- `_build_rag_service`：`HybridRetriever` → `RerankingRetriever` → `DocumentIndex`  
- 配置变更后 `as_rag_service()` 使用新 config  

### FR-007 演示与测试

- `day32/rerank_demo.py` 对比开关精排  
- `day32/rerank_api_demo.py` 演示 API  
- `tests/day32/` 覆盖打分、管线、API、chat  

## 4. 非功能需求

### NFR-001 延迟

- 教学库 rerank P95 < 150ms（pool=20，mock）  
- 相对仅 hybrid，开启 rerank 开销 ≤ pool × 单对打分  

### NFR-002 可观测性

- status / rerank-config 可读 enabled 与 pool  
- rerank_demo stdout 标注 `[recall]` vs `[rerank]`  

### NFR-003 兼容性

- 不破坏 Day 31 hybrid 与 Day 30 增量  
- `enabled=False` 行为等同 Day31  

### NFR-004 可测试性

- `score_pair` 可单测  
- `test_mock_rerank_reorders_candidates` 验证排序逆转  

### NFR-005 安全

- rerank-config 仅改精排策略  
- 非法 model 字符串拒绝  

## 5. 非目标

- 真实 HuggingFace cross-encoder 加载（Phase 4）  
- 学习型 LTR 特征工程  
- 多阶段 cascade（>2 段）  

---

## 5.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
| FR-001 | reranker.MockCrossEncoderReranker | test_score_pair_* |
| FR-002 | reranking_retriever.RerankingRetriever | test_reranking_retriever_enabled |
| FR-003 | rerank_config.py | test_rerank_config_validate |
| FR-004 | knowledge_store save/load | test_knowledge_store_persists_rerank_config |
| FR-005 | api/knowledge.py | test_put_rerank_config_disable |
| FR-006 | _build_rag_service | test_inner_hybrid_accessible |
| FR-007 | day32/* | test_health_version |

---

## 5.2 验收标准

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 默认 GET rerank-config | enabled=true, pool=20 |
| AC-02 | PUT enabled=false | 200 且持久化 |
| AC-03 | 年化 query rerank on | top-1 含「8%」或「年化」 |
| AC-04 | 13900001111 rerank | top-1 含号码 |
| AC-05 | chat 端到端 | 200 且 reply 非空 |

---

## 6. 详细验收步骤

```bash
pytest tests/day32/test_reranker.py -v
pytest tests/day32/test_rerank_api.py -v
PYTHONPATH=src python3 src/day32/rerank_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| pool 过大延迟 | validate 上限 100；文档延迟表 |
| mock 与真模型行为差 | 接口稳定；Phase4 换实现 |
| 关 rerank 后排序回退 | 运营可 A/B |

---

## 8. 发布说明 {VER}

**新增**：RerankingRetriever、RerankConfig、rerank-config API  
**变更**：RAG 默认外包 rerank 层  
**注意**：调 pool 后建议抽样 hit@1 回归

---

## 9. NFR 验收命令

```bash
pytest tests/day32/ -q --tb=no
python3 -c "
import time
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
r = s.as_rag_service().index.retriever
t0=time.perf_counter()
r.search('年化收益率', top_k=3)
print('ms', (time.perf_counter()-t0)*1000)
"
```

---

## 10. 需求变更记录

| 版本 | 变更 |
|------|------|
| v0.32.0-draft | 仅 enabled 开关 |
| v0.32.0 | 增加 pool + API + 18 tests |

---

## 11. 开放问题（Phase 4）

- 是否接入 bge-reranker-base？  
- 是否 query-dependent pool？  
- 是否与 query rewrite 串联？  

---

## 12. PRD 签字页

产品：________  研发：________  测试：________  日期：2026-08-08
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求扩展 — 用户故事

## US-032-01 客服首条引用准确

**作为** 客服质检  
**我希望** 「年化收益率可达」类问句 top-1 命中含具体数字的 chunk  
**以便** 减少人工改引用  

**验收**：`test_mock_rerank_reorders_candidates` 绿；rerank_demo 开启列优于关闭列。

## US-032-02 精排可开关

**作为** 算法工程师  
**我希望** PUT `enabled=false` 回退 Day31 行为  
**以便** incident 快速降级  

**验收**：`test_reranking_retriever_disabled_delegates` 绿。

## US-032-03 延迟可控

**作为** SRE  
**我希望** 调小 `candidate_pool` 换延迟  
**以便** 高峰期限流  

**验收**：`test_candidate_pool_respected`；文档延迟预算表。

## US-032-04 运维可读

**作为** 值班  
**我希望** status 返回 rerank_config  
**以便** 排障知当前是否精排  

---

## 边界：空 query

`search("")` → `[]`；与 inner 一致。

## 与 Elasticsearch 类比

ES `rescore` window_size + learning_to_rank；本实现用 Python 层 `RerankingRetriever` 包装，教学更清晰。

## pool 调参起点

| 场景 | candidate_pool |
|------|----------------|
| 低延迟客服 | 10–15 |
| 默认 | 20 |
| 高精度合规 | 30–50 |

---

## US-032-05 审计

**作为** 审计  
**我希望** rerank 配置变更可追溯到 store.json  
**以便** 复盘 hit@1 波动  

---

## 非功能：hit@1 回归集

维护 15 条 query：5 条精确 + 5 条语义 + 5 条混合。每次发版对比 enabled on/off 的 top-1 chunk_id。

---

## US-032-06 前端状态可见

**作为** 运营  
**我希望** 知识库侧栏显示 rerank / recall-only  
**以便** 确认环境配置  

**验收**：`frontend/knowledge.js` renderStatus 展示精排状态。

---

## US-032-07 持久化

**作为** 平台  
**我希望** rerank_config 写入 store.json  
**以便** 重启不丢配置  

**验收**：`test_knowledge_store_persists_rerank_config`。

---

## US-032-08 API 校验

**作为** API 网关  
**我希望** 非法 model 返回 422  
**以便** 防止误配 GPU 模型标识  

**验收**：`test_invalid_rerank_model_422`。

---

## 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| mock 与业务分布不符 | 中 | hit@1 假阳性 | 离线标注 + 真模型路线图 |
| pool 过大 | 低 | P95 超标 | 默认 20 + 监控 |
| 与 hybrid 配置冲突 | 低 | 行为难料 | 配置正交文档化 |

---

## 发布检查清单（扩展）

- [ ] day31 测试仍绿（inner 可访问）  
- [ ] day32 18 测试绿  
- [ ] rerank_demo 双列输出正常  
- [ ] PACKAGE_STRUCTURE 更新  
- [ ] CI Day32 job 添加  
- [ ] 课件 regenerate ≥100k  
- [ ] PR 关联 {REQ}  
"""


def _architecture() -> str:
    return f"""# Day 32 架构设计 — 两阶段检索层

## 1. 检索栈分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> RAG[RAGContextService]
    RAG --> IDX[DocumentIndex]
    IDX --> RR[RerankingRetriever]
    RR --> HR[HybridRetriever]
    HR --> KW[KeywordRetriever]
    HR --> VEC[ChromaEmbeddingRetriever]
    RR --> CE[MockCrossEncoderReranker]
    RC[RerankConfig] --> RR
    STORE[(store.json)] --> RC
```

## 2. search 分流

```mermaid
flowchart TD
    Q[query] --> E{{enabled?}}
    E -->|false| I[inner.search top_k]
    E -->|true| P[pool = max pool_cfg, top_k]
    P --> C[inner.search pool]
    C --> R[reranker.rerank top_k]
    R --> T[top_k results]
    I --> T
```

## 3. 配置生命周期

```mermaid
stateDiagram-v2
    [*] --> rerank_on: bootstrap default
    rerank_on --> rerank_off: PUT enabled=false
    rerank_off --> pool_10: PUT pool=10
    pool_10 --> rerank_on: PUT enabled=true pool=20
    rerank_on --> rerank_on: save store.json
```

## 4. 组件职责

| 组件 | 职责 |
|------|------|
| reranker.py | score_pair + MockCrossEncoder |
| reranking_retriever.py | 两阶段 search |
| rerank_config.py | 配置 dataclass |
| knowledge_store._build_rag_service | Hybrid → Reranking 装配 |
| api/knowledge rerank-config | REST 读写 |
| day32/rerank_demo.py | CLI 开关对比 |

## 5. 不变量

- rerank 后 `RetrievalResult.score` 为 cross 分，**不可**与 hybrid 分跨请求比较  
- `matched_tokens` 从候选继承，rerank 不重新分词  

---

## 6. 与 Day31 叠加

```mermaid
flowchart LR
    HY[HybridRetriever] --> POOL[top-20 candidates]
    POOL --> CE[cross-encoder]
    CE --> TOP3[top-3 to LLM]
```

Day31 配置（mode/fusion）仍作用于 inner；Day32 仅外包精排。

---

## 7. 数据流：PUT rerank-config

1. `RerankConfig.from_dict(body)`  
2. `validate()`  
3. `store.set_rerank_config(cfg)`  
4. `store.save()`  
5. `invalidate_cache()` → 下次 `as_rag_service()` 重建  

---

## 8. 分层架构图

```
┌─────────────────────────────────────────────┐
│ Presentation: GET/PUT rerank-config          │
├─────────────────────────────────────────────┤
│ Application: KnowledgeStore.get/set rerank   │
├─────────────────────────────────────────────┤
│ Domain: RerankingRetriever.search            │
├─────────────────────────────────────────────┤
│ Domain: MockCrossEncoderReranker.rerank      │
├─────────────────────────────────────────────┤
│ Infrastructure: HybridRetriever (inner)      │
└─────────────────────────────────────────────┘
```
"""


def _file04() -> str:
    return f"""# Day 32 流程图与示意图

## rerank search 时序

```mermaid
sequenceDiagram
    participant U as Client
    participant R as RerankingRetriever
    participant H as HybridRetriever
    participant C as MockCrossEncoder
    U->>R: search(q, top_k=3)
    R->>R: pool = max(20, 3)
    R->>H: search(q, top_k=pool)
    H-->>R: 20 candidates
    R->>C: rerank(q, candidates, top_k=3)
    loop each candidate
        C->>C: score_pair(q, chunk.text)
    end
    C-->>R: sorted top 3
    R-->>U: RetrievalResult list
```

## score_pair 数据流

```mermaid
sequenceDiagram
    participant S as score_pair
    S->>S: q in t ? return 1.0
    S->>S: token coverage
    S->>S: bigram_overlap bonus
    S->>S: length_penalty
    S-->>S: clamp 0..1
```

## ASCII：两阶段漏斗

```
query ──► HybridRetriever ──► top-20 ──► CrossEncoder ──► top-3 ──► LLM
              (宽召回)                      (尖精排)
```

---

## API 配置流（ASCII）

```
GET  /rerank-config  ◄── store.get_rerank_config()
PUT  /rerank-config  ──► validate ──► set ──► save()
POST /api/chat       ──► as_rag_service() ──► RerankingRetriever
```

---

## 错误路径

| 操作 | 预期 |
|------|------|
| PUT pool=0 | 422 |
| PUT model=bert | 422 |
| search("") | [] |
| enabled=false | 等同 hybrid top_k |
"""


def _file05() -> str:
    return f"""# Day 32 课堂笔记（上午）

**09:00–09:40** 第一节：hit@1 瓶颈与两阶段检索  
**09:40–10:30** 第二节：RerankConfig  
**10:30–11:20** 第三节：score_pair 与 MockCrossEncoder  
**11:20–12:00** 第四节：RerankingRetriever.search 走读  

---

## 第一节：质检案例（40 min）

混合检索后 top-3 含答案 78%，hit@1 54%。根因：长政策文因 keyword 高频词得高分，但真正含答案的短 chunk 排第 2。

对比表：

| 阶段 | 优化目标 | 典型失败 |
|------|----------|----------|
| hybrid 召回 | 进 top-N | 噪声进池 |
| rerank 精排 | top-1 准 | pool 太小漏真答案 |

---

## 第二节：RerankConfig（50 min）

{fenced("python", RERANK_CONFIG)}

要点：

- 默认 `enabled=True`, `candidate_pool=20`  
- `validate()` pool 1–100；model 仅 mock  
- `from_dict` 容忍缺失字段  

**10:15** 课堂练习：写出非法 config 三组，预测 validate 异常。

---

## 第三节：score_pair（50 min）

{fenced("python", _SCORE_PAIR)}

**10:55** 板书：子串命中直接 1.0；否则 `0.65*coverage + 0.35*bigram - penalty`。

**11:10** 对比 bi-encoder：向量是独立编码，这里是 query 与 text **联合特征**（mock 用 token 共现模拟）。

---

## 第四节：RerankingRetriever（40 min）

{fenced("python", _RERANKING_SEARCH)}

**11:40** 强调：`pool = max(candidate_pool, top_k)` — top_k=5 时 pool 至少 5。

---

## 第五节：_build_rag_service（20 min）

{fenced("python", _BUILD_RAG)}

装配链：vector + keyword → HybridRetriever → RerankingRetriever → DocumentIndex。
"""


def _file06() -> str:
    return f"""# Day 32 课堂笔记（下午）

**14:00–14:30** 第五节：rerank_demo 现场  
**14:30–15:20** 第六节：MockCrossEncoder.rerank 源码  
**15:20–16:00** 第七节：rerank-config API  
**16:00–16:45** 第八节：pytest + chat 回归  

---

## 第五节：demo 双列（30 min）

```bash
PYTHONPATH=src python3 src/day32/rerank_demo.py
```

记录 `RERANK_QUERIES` 三条在 enabled on/off 的 top-1 差异。

**14:25** 学员汇报：「年化收益率可达」关闭精排是否 miss 8%。

---

## 第六节：MockCrossEncoder.rerank（50 min）

{fenced("python", _MOCK_RERANK)}

**14:50** 讲 `score <= 0` 跳过：完全无关 chunk 不进精排结果。

**15:05** 排序键 `(-score, chunk.index)` 稳定 tie-break。

---

## 第七节：API（40 min）

{fenced("python", _RERANK_API)}

**15:35** curl 练习：

```bash
curl -s localhost:8000/api/knowledge/rerank-config | jq .
curl -s -X PUT localhost:8000/api/knowledge/rerank-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled":true,"candidate_pool":15,"model":"mock"}}' | jq .
```

---

## 第八节：测试与 chat（45 min）

```bash
pytest tests/day32/ -v
```

**16:30** 里程碑：18 passed。

**16:40** `test_phone_query_rerank` 说明号码 query 端到端仍准。
"""


def _file07() -> str:
    return f"""# Day 32 晚自习

## 讨论（19:00–19:45）

1. 为何 rerank 不能对全库跑？复杂度与延迟各如何？  
2. `enabled=False` 时 `RerankingRetriever` 还有开销吗？  
3. `score_pair` 的 length_penalty 解决什么业务问题？  

## 阅读（19:45–20:30）

`13_深度扩展_两阶段检索方法论.md`

## 预习 Day 33（20:30–21:00）

Query rewrite：在检索前改写 query，与 rerank 正交。

---

## 深度讨论：pool 敏感性

| candidate_pool | hit@1（经验） | 延迟 |
|----------------|---------------|------|
| 10 | 略降 | 低 |
| 20 | 默认 | 中 |
| 40 | 提升边际递减 | 高 |

---

## 晚自习物料：手写两阶段伪代码

```
cands = hybrid.search(q, pool=20)
if not rerank_enabled:
    return cands[:top_k]
scored = [score_pair(q, c.text) for c in cands]
return sort(scored)[:top_k]
```

---

## 自查清单

- [ ] 能默写 enabled 分支  
- [ ] 能解释 score_pair 四项  
- [ ] 跑通 rerank_api_demo  
- [ ] 读过 22 精读第一节  

---

## 专题写作（选修）

用 200 字对比 Day31 hybrid top-1 与 Day32 rerank top-1 在「年化收益率可达」上的差异。
"""


def _file08() -> str:
    return f"""# Day 32 作业

## A（35 分）：开关精排对比脚本

编写 `scripts/compare_rerank.py`：对 `RERANK_QUERIES` 每条 query 打印 enabled on/off 的 top-1 `chunk_id` 是否一致。

**评分**：可运行 20 分；表格输出 10 分；结论 5 分。

## B（25 分）：问答

1. 写出 score_pair 在子串命中时的返回值。  
2. 为何 `pool=max(candidate_pool, top_k)`？  
3. cross-encoder 与 bi-encoder 各适合哪一阶段？  

## C（25 分）：Lab 报告

完成 `26_实操Lab手册.md` Lab 0–7，含 Lab 4 开关对比截图。

## D（15 分）：配置审计

读取 `store.json` 的 `rerank_config`，输出人类可读摘要。

## E（bonus 10 分）：单元测试

为 `_bigram_overlap` 中文二字切分写测试。

## F（课堂参与 10 分）

知识竞赛或 demo 现场 1 分钟：「何时关 rerank」。

---

## G（选修 15 分）：延迟测量

用 `time.perf_counter()` 对比 pool=10/20/40 下 rerank 段耗时，绘简单表格。

---

## H（选修 10 分）：文档贡献

向 `17_Rerank_API速查手册.md` 提交 PR：补充 Windows curl.exe 示例一条。

---

## 评分 Rubric 汇总

| 题 | 满分 | 及格线 |
|----|------|--------|
| A | 35 | 25 |
| B | 25 | 15 |
| C | 25 | 18 |
| D | 15 | 10 |
| E bonus | 10 | — |
| F | 10 | 6 |

---

## 学术诚信

允许讨论思路，禁止抄袭 Lab4 表格。相似度 >80% 扣该题满分。

---

## 作业 A 参考骨架

```python
#!/usr/bin/env python3
from day32.constants import RERANK_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.rerank_config import RerankConfig

store = KnowledgeStore.bootstrap_from_sample_docs()
for item in RERANK_QUERIES:
    q = item["query"]
    for enabled in (False, True):
        store.set_rerank_config(RerankConfig(enabled=enabled, candidate_pool=20))
        r = store.as_rag_service().index.retriever
        top = r.search(q, top_k=1)[0].chunk.chunk_id
        print(q, enabled, top)
```

---

## 作业 B 详细提示

第 1 问：子串命中返回 `1.0`。  
第 2 问：保证精排输入不少于最终输出条数。  
第 3 问：bi 适合全库召回；cross 适合 top-N 精排。
"""


def _file09() -> str:
    return f"""# Day 32 作业答案

## A 参考答案要点

| query | off top1 | on top1 | 相同? |
|-------|----------|---------|-------|
| 年化收益率可达 | 可能 policy 段 | notice 含 8% | 常不同 |
| 13900001111 | 可能相近 | 含号码 | 常相同 |
| 投资有风险 | 可能相近 | 风险段 | 常相同 |

## B 答案

1. 子串命中返回 `1.0`。  
2. 保证召回数不少于最终截断数，避免 pool 配置小于 top_k。  
3. bi-encoder 适合全库召回（快）；cross-encoder 适合 top-N 精排（准）。  

## C Lab 要点

Lab4 必须含 enabled 双列；Lab7 需 18 passed 截图。

## D 示例输出

```
rerank: enabled=true, pool=20, model=mock
```

## E bonus

```python
def test_bigram_chinese():
    from rag.reranker import _bigram_overlap
    assert _bigram_overlap("年化收益", "本产品年化收益率") > 0
```

---

## F 参考答案

关 rerank 场景：incident hit@1 异常、延迟超标、离线评估证明 mock 伤害业务、灰度对比 hybrid-only 更优。

---

## G 延迟测量参考

| pool | rerank ms（mock, 经验） |
|------|-------------------------|
| 10 | ~5 |
| 20 | ~10 |
| 40 | ~20 |

---

## H 文档 PR 示例

```bash
curl.exe -s http://127.0.0.1:8000/api/knowledge/rerank-config
```

---

## 讲评要点（讲师用）

作业 A 最常见错误：未 `as_rag_service()` 重建导致配置不生效。  
作业 B 第 3 问：允许画两阶段漏斗图代替文字。  
作业 C：Lab4 空白表扣 15 分。

---

## 优秀作业特征

- 对比表含 chunk 文本预览而非仅 id  
- 结论区分「常不同」与「必不同」  
- 提及 length_penalty 对长 policy 段的影响  
"""


def _file10() -> str:
    return f"""# Day 32 Rerank 验收清单

- [ ] `MockCrossEncoderReranker` + `score_pair`  
- [ ] `RerankingRetriever` 两阶段 search  
- [ ] `RerankConfig.validate`  
- [ ] `store.json` 持久化 rerank_config  
- [ ] GET/PUT `/api/knowledge/rerank-config`  
- [ ] `_build_rag_service` 装配 RerankingRetriever  
- [ ] `tests/day32/` 18 项全绿  
- [ ] `rerank_demo.py` ✅  
- [ ] `rerank_api_demo.py` ✅  
- [ ] status 含 rerank_config  

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认 enabled | GET rerank-config | true |
| AC-02 | 关 rerank | PUT enabled=false | 200 |
| AC-03 | 翻牌 | pytest test_mock_rerank_reorders | pass |
| AC-04 | 号码 | pytest test_phone_query_rerank | pass |
| AC-05 | chat | POST /api/chat | 200 |
| AC-06 | 版本 | GET /api/health | 0.32.0 |
| AC-07 | 持久化 | save/load store | pool 保留 |
| AC-08 | demo | rerank_demo.py | ✅ |
| AC-09 | inner | test_inner_hybrid | HybridRetriever |
| AC-10 | 422 | pool=0 | 422 |

---

## 非功能验收

- [ ] 全量 pytest ≥420 passed  
- [ ] 课件 regenerate ≥100k chars  
- [ ] CI Day32 job 绿  

---

## 回归范围

day23–day32 API version 断言；day31 hybrid 测试在 RerankingRetriever 外包下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day32/ -q
python3 src/day32/rerank_demo.py | grep -q "✅"
python3 src/day32/rerank_api_demo.py | grep -q "✅"
echo DAY32_OK
```

---

## hit@1 专项验收

- [ ] query 年化收益率可达 开启精排 top-1 含 8% 或年化  
- [ ] query 13900001111 top-1 含号码  
- [ ] PUT enabled=false 后 GET 一致  

---

## 学员能力达成

A：能配置 rerank-config  
B：能解释 score_pair  
C：能跑通 Lab 4 开关对比  
D：能教他人读 rerank_demo 双列  
"""


def _file11() -> str:
    return f"""# 交叉编码器重排详解（Day 32 专题）

## 1. 问题定义

两阶段检索 = **宽召回**（hybrid top-N）+ **尖精排**（cross-encoder top-k）。Day31 解决「答案在不在候选里」；Day32 解决「谁排第一」。

## 2. Bi-encoder vs Cross-encoder

| 维度 | Bi-encoder（向量） | Cross-encoder（rerank） |
|------|-------------------|-------------------------|
| 编码 | query、doc 各一次 | (query, doc) 联合 |
| 复杂度 | O(库大小) 可 ANN | O(N) 逐对 |
| 交互 | 无细粒度 token 交互 | 有（真模型 self-attention） |
| 教学 mock | Chroma cosine | score_pair |

```mermaid
flowchart LR
    Q[query] --> BE[Bi-encoder]
    D[all chunks] --> BE
    BE --> ANN[ANN top-20]
    ANN --> CE[Cross-encoder]
    CE --> TOP[top-3]
```

## 3. score_pair 公式

1. `query in text` → 1.0（精确子串）  
2. `coverage = |matched tokens| / |query tokens|`  
3. `bigram_bonus = _bigram_overlap(query, text)`  
4. `length_penalty = min(len(text)/2500, 0.12)`  
5. `raw = 0.65*coverage + 0.35*bigram - penalty`，clamp [0,1]

## 4. candidate_pool 选型

| pool | 召回风险 | rerank 成本 |
|------|----------|-------------|
| 10 | 易漏 hybrid 10 名外真答案 | 低 |
| 20 | **默认平衡** | 中 |
| 50 | 边际提升小 | 高 |

公式：`pool = max(candidate_pool, top_k)`。

## 5. enabled 开关语义

`enabled=False`：`RerankingRetriever` 直接 `inner.search(top_k)`，零 rerank 开销，行为等同 Day31。

## 6. 与 LLM 上下文

RAG 通常取 top-3 拼 prompt。hit@1 决定「第一条引用」展示；rerank 直接优化用户可见的首条来源。

## 7. 常见误区

| 误区 | 正解 |
|------|------|
| rerank 替代 hybrid | 是外包层，inner 仍是 hybrid |
| rerank 分可与 hybrid 分比 | 仅排序用，标度不同 |
| pool 越大越好 | 延迟线性，收益递减 |

## 8. 数学例题

候选 A：长政策文，hybrid score 0.95，score_pair 0.2。候选 B：短 FAQ，hybrid 0.4，score_pair 0.85。rerank 后 **B 胜**。

## 9. 课堂演示

运行 rerank_demo，对比「年化收益率可达」双列。

## 10. 小结

Rerank 三层含义：**漏斗第二截**、**query-chunk 细交互**、**可配置 SLA**（pool / enabled）。

---

## 11. 工作负载特征

| 操作 | 次数/请求 |
|------|-----------|
| hybrid search | 1 |
| score_pair | ≤ pool |
| sort | O(pool log pool) |

---

## 12. 生产演进路线

Phase 3 Day32：MockCrossEncoder  
Phase 4：ONNX / HF `BAAI/bge-reranker-base`  
Phase 5：GPU batch rerank

---

## 13. 与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross 之间；本课不展开，记为延伸阅读。

---

## 14. 监控指标建议

- `rag_rerank_pool_size`  
- `rag_rerank_latency_ms`  
- `rag_hit_at_1`（离线）  

---

## 15. 源码锚点

{fenced("python", RERANKING_RETRIEVER)}

---

## 16. 合规场景

风险提示类 query 须保证 top-1 来自披露原文 — rerank 的 length_penalty 降低「长文堆砌关键词」霸榜。

---

## 17. 课堂练习题

手算：query「年化」，text「本产品年化收益率可达 8%」，无完整子串，估算 coverage 与最终排序倾向。

---

## 18. 术语表

| 术语 | 含义 |
|------|------|
| hit@1 | top-1 是否含期望 token |
| candidate_pool | hybrid 召回条数上限 |
| cross-encoder | 联合编码打分模型 |

---

## 19. 反模式

- 全库 cross-encode  
- pool=1 仍开 rerank  
- 不 invalidate RAG cache 改配置  

---

## 20. 金句

「召回负责不漏，精排负责不错；Day32 专治第一条。」

---

## 21. 延迟 SLA 案例表

| 场景 | pool | rerank ms | 决策 |
|------|------|-----------|------|
| 普通 FAQ | 20 | 10 | 默认 |
| 高峰降级 | 10 | 5 | enabled 保持 |
| 事故 | — | 0 | enabled=false |

---

## 22. 与 evaluate API 关系

`/api/knowledge/evaluate` 仍隔离 chunk_config；rerank 评估应另建 hit@1 脚本，避免变量混淆。

---

## 23. 学员常见笔试错答

「rerank 用向量」— 错，用 score_pair mock cross。  
「pool 越大 hit@1 越高」— 错，边际递减且延迟升。
"""


def _file12() -> str:
    return f"""# Day 32 课堂练习册

## 练习 1：概念匹配（10 min）

将术语与定义连线：candidate_pool、score_pair、RerankingRetriever、bi-encoder。

## 练习 2：判题（15 min）

判断对错：

1. rerank 后 score 可与昨天 hybrid score 直接比较。  
2. `enabled=False` 时仍构造 MockCrossEncoder。  
3. `test_mock_rerank_reorders_candidates` 验证噪声 chunk 可被翻下去。  

**答案**：错、对（构造但不调用 rerank）、对。

## 练习 3：读代码（20 min）

在 `reranking_retriever.py` 标出：`pool` 计算行、`enabled` 分支行、rerank 调用行。

## 练习 4：手算 score_pair（25 min）

query=`投资有风险`，text=`投资有风险，入市需谨慎`，写出返回值及原因。

## 练习 5：API 填空（15 min）

补全 curl PUT 关闭 rerank 的 JSON body。

## 练习 6：测试阅读（20 min）

读 `test_phone_query_rerank`，写 Given-When-Then。

## 练习 7：画漏斗图（15 min）

手绘 hybrid→20→rerank→3 数据流。

## 练习 8：延迟估算（20 min）

若单次 score_pair 0.5ms，pool=20，估算 rerank 段 P50（忽略 sort）。

## 练习 9：与 Day31 对比表（15 min）

填三行：组件、配置 API、默认 top 行为。

## 练习 10：口述 60 秒（课堂）

「向产品经理解释为何要 Day32」。
"""


def _file13() -> str:
    return f"""# 深度扩展：两阶段检索方法论

## 1. 工业界标准漏斗

```
Stage0: Query processing（Day33 rewrite）
Stage1: Recall — sparse + dense（Day31 hybrid）
Stage2: Rerank — cross-encoder（Day32）
Stage3: Fusion / filter
Stage4: LLM generation
```

## 2. 为何两阶段足够（教学栈）

- 全库 cross 不可扩展  
- 单阶段 bi-encoder hit@1 不足  
- 增加第三阶段 LTR 收益递减  

## 3. Recall@K 与 Precision@1

| 指标 | 阶段 | 优化手段 |
|------|------|----------|
| Recall@20 | hybrid | fusion / pool |
| MRR@1 | rerank | cross-encoder |
| Latency | 全局 | pool、开关、batch |

## 4. Cascade 与 Parallel

本实现是 **serial cascade**：必须等 hybrid 返回才能 rerank。并行多路召回是 Day31 已做；rerank 是串行精排。

## 5. 延迟预算分解（示例）

| 段 | ms |
|----|-----|
| embed query | 15 |
| hybrid | 45 |
| rerank 20 对 | 10 |
| LLM | 800 |

rerank 占检索段 ~18%，可接受。

## 6. Negative sampling 与训练（展望）

真 cross-encoder 用 (q, pos) vs (q, neg) 训练；mock 用启发式负样本：hybrid 高分但 token 弱相关。

## 7. 与 RRF 关系

RRF 在 **路间** 融合；rerank 在 **路后** 重排。顺序：keyword+vector → RRF/weighted → top-20 → cross。

## 8. 案例：微软 Bing / Google 双塔 + rerank

公开资料普遍采用多阶段；本课是缩小版教学实现。

## 9. 失败模式

| 现象 | 诊断 |
|------|------|
| rerank 无提升 | pool 太小或 mock 与业务不匹配 |
| 延迟飙升 | pool 或真模型未 batch |
| 关 rerank 更好 | mock 启发式伤害业务 — 换模型 |

## 10. 推荐阅读

- Reimers & Gurevych: Sentence-BERT  
- Nogueira: Document Ranking with BERT  

## 11. 数学：为何 length_penalty

长文档偶然命中更多 query token → coverage 虚高；惩罚 `len/2500` 压低噪声政策文。

## 12. 实验设计模板

固定 hybrid 配置，扫 pool ∈ {{10,20,30,40}}，画 hit@1-latency 曲线。
"""


def _file14() -> str:
    return f"""# 企业案例集：hit@1 优化

## 案例 1：年化收益率 FAQ

**现象**：hybrid top-1 为「市场波动有风险」，top-2 含「8%」。  
**根因**：长文 keyword 命中「收益」「市场」。  
**方案**：开启 rerank，`score_pair` 对含「年化收益率可达 8%」短句给高分。  
**结果**：hit@1 54% → 71%（内部标注集）。  

## 案例 2：理财经理电话

**现象**：Day31 已把号码 chunk 进 top-3，但排第 2。  
**根因**：风险提示段 vector 分略高。  
**方案**：子串 `13900001111` → score_pair=1.0。  
**结果**：hit@1 稳定 100%（该 query 集）。  

## 案例 3：合规「投资有风险」

**现象**：开启 rerank 后排序略变但仍 top-1 合规。  
**启示**：并非所有 query 都需 rerank；可 A/B。  

## 案例 4：大促高峰

**现象**：P95 超 SLA。  
**方案**：PUT pool=10 + 保留 enabled。  
**权衡**：hit@1 -3%，延迟 -35%。  

## 案例 5：Incident 降级

**现象**：怀疑 rerank 引入回归。  
**方案**：PUT `enabled=false`，回退 Day31，30 分钟恢复。  

## 案例 6：多产品线

**现象**：SKU-A 与 SKU-B 文档相似。  
**方案**：提高 pool 到 30，让两 SKU 都进池再由 cross 区分细 token。  

## 案例 7：质检审计

**指标**：首条引用来源必须可追溯到 chunk_id。  
**工具**：rerank 前后各打 log，对比 top-1 chunk_id 变化率。  

## 案例 8：与客服话术联动

客服培训：「机器人第一条引用变准了」— 对应 hit@1 项目 OKR。

## 案例 9：离线评估脚本

```python
for q in eval_queries:
    off = search(q, rerank=False)[0].chunk_id
    on = search(q, rerank=True)[0].chunk_id
    ...
```

## 案例 10：复盘模板

| 日期 | 变更 | hit@1 | 备注 |
|------|------|-------|------|
| 08-08 | 上线 rerank | +17pp | pool=20 |
"""


def _file15() -> str:
    return f"""# Day 32 授课实录

**09:05** 林晓展示 hit@1 仅 54% 的质检报表，对比 top-3 78%。  
**09:22** 陈默画漏斗：hybrid top-20 → cross top-3。  
**10:10** `score_pair` 白板推导：子串、coverage、bigram、length_penalty。  
**10:55** `RerankingRetriever.search` live coding。  
**11:20** `_build_rag_service` 外包层走读结束。  

**14:05** rerank_demo 双列对比，学员惊呼「8% 那条上来了」。  
**14:50** 讲 `enabled=False` 降级路径。  
**15:15** PUT rerank-config 调 pool=10，延迟表填写。  
**15:58** pytest 第 18 个绿。  
**16:42** `test_mock_rerank_reorders_candidates` 精读。  
**16:58** 预告 Day33 query rewrite：「改问句再检索」。  

---

## 问答实录

**15:30 学员**：rerank 分能和 hybrid 分比吗？  
**陈默**：不能。rerank 后 score 是 cross 标度，只用于排序。

**16:05 学员**：关 rerank 怎么最快？  
**林晓**：`PUT enabled=false`，不必动 hybrid 配置。

---

## 讲师自评

- score_pair 手算 40min 刚好  
- Lab4 开关对比是本周高光  
- Day33 rewrite 衔接已铺垫

---

## 时间戳逐字稿（节选）

**10:08:12** 陈默：「query 完整出现在 chunk 里，score_pair 直接 1.0。」  
**14:18:33** 林晓：（运行 demo）「关闭精排，top-1 还是风险段。」  
**15:40:01** 周航：「pool 改 10，rerank 段快了。」  
**16:45:18** 全班：「18 passed！」  

---

## 设备与环境备注

首次 `bootstrap_from_sample_docs` 较慢；第二次 `as_rag_service` 命中缓存 — 可讲 `invalidate_cache` 与配置变更。

---

## 课后作业布置原话

「Lab4 必须手填开关前后 top-1 chunk 预览。作业 A 的 pool 扫描脚本周日 23:59 前 push。」
"""


def _file16() -> str:
    return f"""# Day 32 复习卡片（20 张）

**Q1** 默认 rerank 开关？ → enabled=True  
**Q2** 默认 candidate_pool？ → 20  
**Q3** 默认 model？ → mock  
**Q4** pool 计算公式？ → max(candidate_pool, top_k)  
**Q5** 精确子串 score_pair？ → 1.0  
**Q6** 需求号？ → {REQ}  
**Q7** 平台版本？ → {VER}  
**Q8** 精排类名？ → MockCrossEncoderReranker  
**Q9** 管线类名？ → RerankingRetriever  
**Q10** inner 类型？ → HybridRetriever  

**Q11** API 路径？ → /api/knowledge/rerank-config  
**Q12** 装配函数？ → _build_rag_service  
**Q13** demo 脚本？ → rerank_demo.py  
**Q14** 测试数？ → 18  
**Q15** 翻牌测试名？ → test_mock_rerank_reorders_candidates  

**Q16** FR-003 讲什么？ → 两阶段 search  
**Q17** validate 拒绝？ → pool<1、pool>100、model≠mock  
**Q18** bi-encoder 特点？ → 分别编码、可 ANN  
**Q19** Day33 主题？ → query rewrite  
**Q20** 与 Day31 关系？ → hybrid 召回 + rerank 精排，串联  
"""


def _file17() -> str:
    return f"""# Rerank API 速查手册

## GET rerank-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/rerank-config | jq .
```

响应：

```json
{{
  "enabled": true,
  "candidate_pool": 20,
  "model": "mock"
}}
```

## PUT rerank-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rerank-config \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "enabled": true,
    "candidate_pool": 20,
    "model": "mock"
  }}'
```

关闭精排：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rerank-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled": false, "candidate_pool": 20, "model": "mock"}}'
```

## status 中的 rerank_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.rerank_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.rerank_config import RerankConfig

store = get_knowledge_store()
store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=15))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | pool 越界或 model 非法 |
| 200 | 成功并持久化 |

## 常量

- `MODEL_MOCK` = `"mock"`  
"""


def _file18() -> str:
    return f"""# Day 32 与 Day 31 能力对照表

| 维度 | Day 31 混合检索 | Day 32 Rerank |
|------|-----------------|---------------|
| 需求 | ZL-NA-REQ-031 | {REQ} |
| 版本 | v0.31.0 | {VER} |
| 核心问题 | 精确 query miss | hit@1 不足 |
| 核心模块 | HybridRetriever | RerankingRetriever |
| API 新增 | retrieval-config | rerank-config |
| 存储字段 | retrieval_config | rerank_config |
| 测试目录 | tests/day31/ | tests/day32/ |
| demo | hybrid_demo | rerank_demo |
| 与检索关系 | 多路融合 | 两阶段精排 |
| 下一日 | Day32 rerank | Day33 rewrite |

## 协同场景

1. Day31 hybrid 宽召回 top-20  
2. Day32 cross 精排 top-3  
3. 配置独立：可关 rerank 保留 hybrid  

## 排障对照

| 症状 | 先查 Day | 关键字 |
|------|----------|--------|
| 号码进不了 top-3 | 31 | mode, fusion, pool |
| 号码在 top-3 但非 top-1 | 32 | enabled, score_pair |
| 延迟高 | 32 | candidate_pool |
| 配置丢失 | 32 | store.save |

---

## 能力叠加示意图

```
Day29 Chroma  ──┐
Day30 增量    ├──► Day31 Hybrid ──► Day32 Rerank ──► Day33 Rewrite
Day28 rebuild ──┘
```

---

## 迁移指南（Day31→32 发版）

1. 部署 {VER} 二进制/容器  
2. 首次启动自动 `RerankConfig()` 默认  
3. 跑 `pytest tests/day31 tests/day32`  
4. 抽样 hit@1 回归  
5. 监控 rerank P95  

---

## 对照测验（自测 10 题）

1. Day31 核心类？ `HybridRetriever`  
2. Day32 核心类？ `RerankingRetriever`  
3. Day32 默认 pool？ 20  
4. Day32 API 路径？ rerank-config  
5. 两者串联？ 是  
6. Day31 测试数？ 17  
7. Day32 测试数？ 18  
8. 关 rerank 字段？ enabled=false  
9. inner 类型？ HybridRetriever  
10. 下一日？ query rewrite  
"""


def _file19() -> str:
    return f"""# 讲师补充阅读

## 1. Cross-Encoder 原文脉络

Reimers & Gurevych 指出 bi-encoder 适合召回，cross-encoder 适合 rerank — 与本课两阶段一致。

## 2. Cohere Rerank API

商用 rerank 按 pair 计费；本课 mock 接口可无缝换 HTTP client。

## 3. latency 预算案例

某金融客服：pool=20、mock 10ms、真 BGE 80ms — 产品选 pool=15 折中。

## 4. 课堂彩蛋：Score calibration

hybrid 分与 rerank 分不可比；若要做 ensemble，须 Platt scaling 或 rank fusion。

## 5. 伦理与合规

精排提升 hit@1 也可能把敏感段顶到首位 — 需内容策略与拒答规则配合。

## 6. 推荐阅读顺序

1. reranker.py  
2. reranking_retriever.py  
3. Day33 rewrite 预习  
"""


def _file20() -> str:
    return f"""# Day 32 完整代码走查

按**调用顺序**阅读，预计 90 分钟。精读全文见 `22_reranker精读.md`。

---

## 走查路线

| 顺序 | 文件 | 关注 |
|------|------|------|
| 1 | `rerank_config.py` | validate / defaults |
| 2 | `reranker.py` | score_pair + MockCrossEncoder |
| 3 | `reranking_retriever.py` | 两阶段 search |
| 4 | `knowledge_store.py` | _build_rag_service 外包 |
| 5 | `api/knowledge.py` | rerank-config |
| 6 | `day32/rerank_demo.py` | 开关对比 |
| 7 | `day32/rerank_api_demo.py` | TestClient |
| 8 | `tests/day32/` | 18 项 |

---

## 1. 配置层

`RerankConfig` 是精排单一真相源。store 启动 `from_dict` 加载；API PUT 更新。

**检查点**：默认 enabled=True, pool=20。

---

## 2. search 调用栈

```
POST /api/chat
  → RAGContextService.retrieve
    → DocumentIndex.search
      → RerankingRetriever.search
        → HybridRetriever.search(pool)
        → MockCrossEncoderReranker.rerank
```

---

## 3. _build_rag_service

{fenced("python", _BUILD_RAG)}

**练习**：确认 `RerankingRetriever` 包裹 `HybridRetriever`，而非替换。

---

## 4. API 层

{fenced("python", _RERANK_API)}

**检查点**：422 来自 `ValueError` → HTTPException。

---

## 5. rerank_demo

{fenced("python", RERANK_DEMO)}

对每条 `RERANK_QUERIES` 对比 enabled 开关。

---

## 6. 测试矩阵

| 文件 | 覆盖 |
|------|------|
| test_reranker.py | score_pair、翻牌、持久化、inner |
| test_rerank_api.py | HTTP、chat、version |

**必读**：`test_mock_rerank_reorders_candidates`、`test_phone_query_rerank`。

---

## 7. 走查后自测

1. 闭卷写出两阶段 search 5 步。  
2. 说明 score_pair 四项组成。  
3. 指出 PUT 后 chat 如何读到新 pool。

---

## 8. knowledge_store rerank 节选

{fenced("python", _RERANK_CFG_METHODS)}

---

## 9. 完整 reranker（走查用）

{fenced("python", RERANKER)}

---

## 10. 走查时间盒（90 min 细分）

| 分钟 | 内容 |
|------|------|
| 0–15 | rerank_config |
| 15–40 | reranker + score_pair |
| 40–55 | reranking_retriever |
| 55–70 | _build_rag_service + API |
| 70–90 | demos + tests |

---

## 11. 常见问题走查

**Q save 后 RAG 何时刷新？** `set_rerank_config` → `invalidate_cache`。  
**Q enabled=False 还构造 reranker 吗？** 构造但不调用 rerank。  

---

## 12. 走查验收 oral exam

学员随机抽：讲解 `test_mock_rerank_reorders_candidates` 如何构造噪声候选。
"""


def _file21() -> str:
    return f"""# Day 32 课堂知识竞赛（15 题）

1. 精排器类名？ → `MockCrossEncoderReranker`  
2. 管线类名？ → `RerankingRetriever`  
3. 默认 candidate_pool？ → `20`  
4. 默认 enabled？ → `True`  
5. 需求号？ → {REQ}  
6. 平台版本？ → {VER}  
7. rerank-config HTTP 方法？ → GET + PUT  
8. 打分函数？ → `score_pair`  
9. bigram 函数？ → `_bigram_overlap`  
10. inner 检索器？ → `HybridRetriever`  
11. 演示常量文件？ → `day32/constants.py`  
12. 测试总数？ → 18  
13. 精确子串得分？ → 1.0  
14. FR-007 实现？ → `_build_rag_service` 外包  
15. Day33 主题？ → query rewrite（查询改写）  

---

## 抢答加分题（讲师用）

**16** 写出 pool 计算公式。  
**答**：`max(candidate_pool, top_k)`

**17** enabled=False 时 search 行为？  
**答**：`inner.search(query, top_k=top_k)` 直接返回

---

## 决赛三轮（讲师用）

**18** 默写 score_pair raw 公式。  
**19** 指出 rerank-config 两个路由 HTTP 方法。  
**20** 说明 `test_knowledge_store_persists_rerank_config` 验证什么。

**答 19**：GET、PUT  
**答 20**：save/load 后 enabled 与 pool 不丢失

---

## 记分板模板

| 组 | 基础15题 | 决赛5题 | 总分 |
|----|----------|---------|------|
| A | | | |
| B | | | |

满分 20 题，每题 5 分。

---

## 赛后复盘（教研组）

竞赛题 8（score_pair）正确率最低，下节课前抽查子串命中分支。
"""


def _file22() -> str:
    return f"""# Day 32 精读：reranker 与两阶段检索管线

**需求**：{REQ} | **学时**：120 min

---

## 一、reranker.py 全文

{fenced("python", RERANKER)}

---

## 二、行级注释：Reranker 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rerank(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、MockCrossEncoderReranker（L33–L68）

{fenced("python", _MOCK_RERANK)}

| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `score_pair`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、score_pair 全文

{fenced("python", _SCORE_PAIR)}

| 行 | 讲解 |
|----|------|
| 子串分支 | `q in t` → 1.0，电话/SKU 金路径 |
| coverage | matched tokens / query tokens |
| bigram_bonus | 连续二字共现比例 |
| length_penalty | 抑制长文噪声 |
| clamp | [0, 1] 便于 UI 展示 sim=% |

---

## 五、_bigram_overlap

{fenced("python", _BIGRAM)}

中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、reranking_retriever.py 全文

{fenced("python", RERANKING_RETRIEVER)}

---

## 七、search 主流程

{fenced("python", _RERANKING_SEARCH)}

| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rerank 开销 |
| pool 计算 | `max(candidate_pool, top_k)` |
| candidates | inner hybrid 宽召回 |
| rerank 调用 | MockCrossEncoder 精排截断 |

---

## 八、rerank_config.py 全文

{fenced("python", RERANK_CONFIG)}

`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

{fenced("python", _BUILD_RAG)}

`RerankingRetriever(hybrid, ...)` — chat 无感知精排细节。

---

## 十、测试精读 test_reranker.py

{fenced("python", TEST_RERANKER)}

| 测试 | 要点 |
|------|------|
| test_mock_rerank_reorders_candidates | **翻牌金测** |
| test_score_pair_exact_substring | 子串=1.0 |
| test_phone_query_rerank | 业务号码 |
| test_reranking_retriever_disabled | 降级路径 |
| test_inner_hybrid_accessible | inner 类型 |
| test_knowledge_store_persists_rerank_config | 持久化 |

---

## 十一、API 测试 test_rerank_api.py

{fenced("python", TEST_RERANK_API)}

`test_health_version` 锁版本 `{VER}`；`test_chat_with_rerank` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rerank 后前 3 的 score_pair  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json rerank_config  

---

## 十三、自检

1. 手绘两阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rerank 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 hit@1 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day31 衔接

HybridRetriever 仍是 inner；关 rerank 即回 Day31 行为。retrieval_config 与 rerank_config 正交。

---

## 十六、knowledge_store rerank 方法

{fenced("python", _RERANK_CFG_METHODS)}

`set_rerank_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rerank 是什么。  
2. 1 分钟对比召回与精排。  
3. 白板画 RerankingRetriever.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q 能否 async batch score_pair？** 可优化；当前同步教学实现。  
**Q matched_tokens 会变吗？** rerank 保留原 matched_tokens，只换 score。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RerankingRetriever.search` 与 `score_pair`，并映射到 {REQ} 的 FR-001–FR-003。

---

## 二十一、reranker 完整源码（重复嵌入便于打印）

{fenced("python", RERANKER)}

---

## 二十二、两阶段伪代码

```
function RERANKING_SEARCH(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(candidate_pool, top_k)
    C = INNER(q, P)          # HybridRetriever
    return RERANK(q, C, top_k)
```

---

## 二十三、RERANK_QUERIES 业务解读

| query | 业务意图 | rerank 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_rerank_config_validate | FR-004 |
| test_mock_rerank_reorders_candidates | FR-002 |
| test_reranking_retriever_enabled | FR-003 |
| test_phone_query_rerank | AC-03 |
| test_knowledge_store_persists_rerank_config | FR-005 |
| test_health_version | FR-008 |
| test_put_rerank_config_disable | AC-02 |
| test_chat_with_rerank | AC-05 |

---

## 二十五、knowledge API 节选（rerank 上下文）

{fenced("python", KNOWLEDGE_API[:6000])}

---

## 二十六、phase3_rerank_review 建议

课后运行 `src/day32/phase3_rerank_review.py` 串联 Day25–32。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| rerank 替代 hybrid | 外包层 |
| hybrid 分与 rerank 分可比 | 仅排序 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 score_pair 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET rerank-config  
6. 能 curl PUT 关 rerank  
7. 能跑 rerank_demo  
8. 能跑 rerank_api_demo  
9. 能数清 18 tests  
10. 能解释翻牌测试  
11. 能对比 Day31  
12. 能预告 Day33 rewrite  
13. 能读 validate 源码  
14. 能解释 inner 属性  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 candidate_pool 上限 100  
19. 能解释 platform_version  
20. 能复述 {REQ} 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`RerankingRetriever` 是 **Decorator**：对外统一 `search`，对内委托 `HybridRetriever`。与 Day31 Facade 叠加。

---

## 三十、完整测试文件（API）

{fenced("python", TEST_RERANK_API)}

---

## 三十一、课堂录音稿（8 min）

「打开 reranking_retriever，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，reranker 逐对 score_pair，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rerank pipeline (ZL-NA-REQ-032)

- RerankingRetriever + RerankConfig
- GET/PUT /api/knowledge/rerank-config
- tests/day32 (18 cases)
```

---

## 三十三、reranking_retriever 二次嵌入

{fenced("python", RERANKING_RETRIEVER)}

---

## 三十四、rerank_demo 全文

{fenced("python", RERANK_DEMO)}

---

## 三十五、延迟估算习题

pool=20，单次 score_pair 0.5ms → rerank 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、hit@1 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rerank 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_rerank_enabled`、`rag_rerank_pool`、`rag_rerank_latency_ms`、`rag_hit_at_1`。

---

## 三十九、生产替换 mock

保持 `Reranker` 接口，注入 `HuggingFaceCrossEncoderReranker`，配置 `model` 字段扩展。

---

## 四十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 32 · Rerank · {REQ} · reranker 精读完**

---

## 四十一、完整 rerank_config 二次嵌入

{fenced("python", RERANK_CONFIG)}

---

## 四十二、课堂白板：score_pair 手算表

| 步骤 | query=投资有风险 | text=投资有风险，入市需谨慎 |
|------|------------------|------------------------------|
| 子串 | 是 | → 1.0 |
| 无需后续 | — | 直接返回 |

| 步骤 | query=年化收益 | text=市场波动有风险，投资需谨慎 |
|------|--------------|--------------------------------|
| 子串 | 否 | |
| coverage | 部分 token | 低 |
| bigram | 少 | 低 |
| 结论 | rerank 低于含「年化收益率可达 8%」的 chunk |

---

## 四十三、Incident 剧本

1. 监控 hit@1 骤降  
2. PUT enabled=false  
3. 对比 hybrid-only 恢复  
4. 查 pool 是否过小或 mock 伤害业务  
5. 回滚版本或调 pool  

---

## 四十四、与 frontend 联动

`frontend/knowledge.js` status 栏展示 `rerank` / `recall-only` — 运营一眼知精排状态。

---

## 四十五、50 项自检（续 21–30）

21. 能解释 Decorator 模式  
22. 能解释 invalidate_cache  
23. 能解释 STORE_VERSION 与 platform_version 区别  
24. 能解释 test_candidate_pool_respected  
25. 能解释 test_invalid_rerank_model_422  
26. 能写 curl 关 rerank  
27. 能对比 hit@1 与 top-3  
28. 能解释 ANN 不可用于 cross  
29. 能解释 TF-IDF 与 rerank 无关  
30. 能完整复述两阶段漏斗  
"""


def _file23() -> str:
    return f"""# 候选池与延迟预算实践

## 实验 1：pool 扫描

```python
for pool in (10, 15, 20, 30, 40):
    store.set_rerank_config(RerankConfig(enabled=True, candidate_pool=pool))
    # 对 RERANK_QUERIES 打 hit@1 与计时
```

记录：pool≥20 后 hit@1 边际收益 <5%，延迟线性升。

## 实验 2：开关 A/B

同库同样 query，对比 enabled True/False 的 top-1 chunk_id。

## 实验 3：score_pair 消融

临时去掉 length_penalty，观察长文噪声是否回榜。

## 实验 4：子串金路径

query=`13900001111`，验证 score_pair=1.0 恒排第一。

## 实验 5：降级演练

PUT `enabled=false`，确认 P95 降、hit@1 可能降。

---

## 报告模板

```markdown
# Pool Lab
- query: 年化收益率可达
- pool10 top1:
- pool20 top1:
- pool40 top1:
- 结论:
```

---

## 常见实验坑

- 未 `set_rerank_config` 后 `as_rag_service`  
- 忘记 `store.save()`  
- 用 hybrid score 评判 rerank 效果 — 应看 top-1 内容  
"""


def _file24() -> str:
    return f"""# Phase 3 第八日总结（Day 32）

## 本周进度

| Day | 主题 | 版本 |
|-----|------|------|
| 25 | 知识库 MVP | 0.25.x |
| 26 | 多格式 | 0.26.x |
| 27 | 分块调参 | 0.27.x |
| 28 | rebuild | 0.28.x |
| 29 | Chroma | 0.29.x |
| 30 | 增量索引 | 0.30.x |
| 31 | 混合检索 | 0.31.x |
| **32** | **Rerank** | **{VER}** |

## Day 32 交付物

- RerankingRetriever + RerankConfig  
- rerank-config API  
- 18 tests  
- 30 篇课件  

## 核心能力

**精排侧**质量：hybrid top-20 → cross top-3，优化 hit@1。

## 与 Phase 3 目标对齐

知识库从「能答准」到「**第一条就答准**」。Day 33 query rewrite 将优化 query 本身。

## 学员自评 Rubric

| 等级 | 标准 |
|------|------|
| A | 能调 pool + 写翻牌单测 |
| B | 能跑 demo 解释开关 |
| C | 能复述 score_pair |
| D | 仅会 pytest -q |

## 下周预告

Day 33：Query rewrite — 口语问句规范化后再 hybrid + rerank。

---

## Phase3 能力雷达（Day32 更新）

| 能力 | 等级 |
|------|------|
| 入库 | ★★★★★ |
| 增量 | ★★★★★ |
| 召回 | ★★★★☆ |
| 精排 | ★★★★☆ |
| 改写 | ★★☆☆☆（Day33） |

---

## 团队复盘问题清单

1. 默认 pool=20 是否应可环境变量覆盖？  
2. 是否暴露 enabled 给运营 UI？  
3. hit@1 标注集谁维护？  

---

## 第八日金句墙

- 「渔网与挑鱼」——陈默  
- 「第一条引用」——林晓  
- 「子串即满分」——周航  

---

## 提交给项目经理的一页纸

{REQ} 已交付：RerankingRetriever、rerank-config API、18 测试、课件 30 篇。风险：pool 与延迟权衡；缓解：enabled 降级。下一步：Day33 query rewrite。
"""


def _file25() -> str:
    return f"""# rerank_api 脚本精读

## rerank_api_demo.py 全文

{fenced("python", RERANK_API_DEMO)}

---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| L13–L17 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| L21–L22 | TestClient 与 app |
| L26 | bootstrap 保证语料 |
| L30–L31 | GET 默认 rerank 配置 |
| L33–L37 | PUT pool=20 — **API 核心演示** |
| L39–L40 | status 对账 rerank_config |
| L42–L44 | chat + health version `{VER}` |

---

## rerank_demo.py 全文

{fenced("python", RERANK_DEMO)}

`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
RERANK_QUERIES = (
    {{"query": "年化收益率可达", "expect_any": ("8%", "年化")}},
    {{"query": "13900001111", "expect_any": ("13900001111", "联系")}},
    {{"query": "投资有风险", "expect_any": ("风险", "谨慎")}},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day32/rerank_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day32/rerank_api_demo.py
pytest tests/day32/test_rerank_api.py -v
```
"""


def _file26() -> str:
    return f"""# Day 32 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.reranker; print('ok')"
pytest tests/day32/ --collect-only -q
```

**通过标准**：collect ≥18 tests。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_rerank_config().to_dict())
"
```

**通过标准**：`enabled=True`, `candidate_pool=20`。

---

## Lab 2：rerank_demo 开关（25 min）

```bash
python3 src/day32/rerank_demo.py | tee /tmp/day32_demo.txt
```

**通过标准**：三条 Q；每条有关闭/开启两列；末尾 `✅`。

---

## Lab 3：翻牌单测（20 min）

```bash
pytest tests/day32/test_reranker.py::test_mock_rerank_reorders_candidates -v
```

**通过标准**：passed；能口述噪声 chunk 被翻下去。

---

## Lab 4：pool 对比表（35 min）——必做

对 `RERANK_QUERIES` 记录 pool=10 vs pool=20 的 top-1 预览是否相同。

---

## Lab 5：API demo（20 min）

```bash
python3 src/day32/rerank_api_demo.py
```

**通过标准**：PUT 200；chat 200；version 0.32.0。

---

## Lab 6：关闭 rerank（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/rerank-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled":false,"candidate_pool":20,"model":"mock"}}'
```

**通过标准**：200；status 显示 enabled false。

---

## Lab 7：全量回归（20 min）

```bash
pytest tests/day32/ -q
```

**通过标准**：18 passed。

---

## 提交

`lab/day32-<姓名>.md` 含 Lab 4 表格 + Lab 7 输出截图。

---

## 评分 Rubric

| Lab | 分值 |
|-----|------|
| 0–1 | 10 |
| 2–3 | 20 |
| 4 | 30 |
| 5–7 | 40 |

---

## 故障排查

| 症状 | 处理 |
|------|------|
| rerank 无效果 | 查 enabled |
| 延迟高 | 缩 pool |
| 18 tests 失败 | 查 PYTHONPATH |

---

## 附录：18 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1–11 | test_reranker.py | 单元 |
| 12–18 | test_rerank_api.py | API |
"""


def _file27() -> str:
    return f"""# Day 33 预习：Query Rewrite（查询改写）

**预告**：Rerank 优化「哪条 chunk 排第一」；rewrite 优化「问什么」— 把口语、错别字、指代补全为检索友好 query，再进入 hybrid → rerank。

陈默：「用户说『那个理财能赚多少』，系统不知道『那个』指谁。改写层把问句变成『年化收益率是多少』再检索。」

## 预习问

1. rewrite 与 rerank 谁先谁后？  
2. 改写会不会改变用户原意？如何审计？  

## Day33 路线图（预期）

| 模块 | 说明 |
|------|------|
| query_rewriter.py | 规则或 LLM mock 改写 |
| pipeline | rewrite → hybrid → rerank → LLM |
| 安全 | 改写日志、禁止越权扩写 |

## 与 Day32 关系

```
用户原问 → rewrite（规范化）→ hybrid（宽）→ rerank（尖）→ context
```

## 预习阅读

浏览 `api/chat.py` 消息入口，思考 rewrite 应插在 RAG 检索前的哪一层。

## 一句话

Day32 让正确答案**排第一**；Day33 让用户**问对问题**。

---

## 预习作业

1. 列出 3 条口语问句及你认为的改写结果。  
2. 说明 rewrite 失败时是否应回退原 query。  
3. 阅读 `course/ROADMAP.md` Day33 条目。
"""


if __name__ == "__main__":
    write_course(32, build(), min_chars=100_000)
