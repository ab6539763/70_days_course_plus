#!/usr/bin/env python3
"""Gold-standard course material builder for Day 31 — 混合检索 hybrid retrieval."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402
from course_mermaid import sanitize_mermaid_blocks  # noqa: E402

REQ = "ZL-NA-REQ-031"
VER = "v0.31.0"
REPO = "nexus-agent-platform/src"

HYBRID_RETRIEVER = read_repo(f"{REPO}/rag/hybrid_retriever.py")
RETRIEVAL_CONFIG = read_repo(f"{REPO}/rag/retrieval_config.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
KNOWLEDGE_API = read_repo(f"{REPO}/api/knowledge.py")
HYBRID_DEMO = read_repo(f"{REPO}/day31/hybrid_demo.py")
HYBRID_API_DEMO = read_repo(f"{REPO}/day31/hybrid_api_demo.py")
TEST_HYBRID = read_repo(f"{REPO}/../tests/day31/test_hybrid_retriever.py")
TEST_HYBRID_API = read_repo(f"{REPO}/../tests/day31/test_hybrid_api.py")

_BUILD_RAG = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def _build_rag_service"): KNOWLEDGE_STORE.find(
        "_store: KnowledgeStore"
    )
]
_RETRIEVAL_API = KNOWLEDGE_API[
    KNOWLEDGE_API.find('@router.get("/retrieval-config"'): KNOWLEDGE_API.find(
        '@router.get("/chunk-config"'
    )
]
_WEIGHTED_MERGE = HYBRID_RETRIEVER[
    HYBRID_RETRIEVER.find("def _weighted_merge"): HYBRID_RETRIEVER.find(
        "def _rrf_merge"
    )
]
_RRF_MERGE = HYBRID_RETRIEVER[
    HYBRID_RETRIEVER.find("def _rrf_merge"): HYBRID_RETRIEVER.find(
        "def _normalize_scores"
    )
]
_HYBRID_SEARCH = HYBRID_RETRIEVER[
    HYBRID_RETRIEVER.find("def search(self"): HYBRID_RETRIEVER.find(
        "def _weighted_merge"
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
        "10_混合检索验收清单.md": _file10(),
        "11_混合检索详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_检索融合方法论.md": _file13(),
        "14_企业案例集_精确SKU查询.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_混合检索API速查手册.md": _file17(),
        "18_与Day30能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_hybrid_retriever精读.md": _file22(),
        "23_RRF与加权融合实践.md": _file23(),
        "24_Phase3第七日总结.md": _file24(),
        "25_hybrid_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day32预习.md": _file27(),
    }
    return files


def _readme() -> str:
    return f"""# Day 31 课件索引

**日期**：2026-08-07（星期五）  
**主题**：混合检索（Hybrid Retrieval）— 关键词 + 向量融合  
**需求**：{REQ}  
**平台版本**：{VER}

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
"""


def _narration() -> str:
    return f"""# Day 31 旁白解读

2026 年 8 月 7 日，星期五。林晓在客服工单里看到一条投诉：「机器人答不出理财经理电话 13900001111。」她切到纯向量模式复现——top-1 落在「风险提示」段落，手机号 chunk 排到第 7。

陈默在白板写下两行：

| 检索腿 | 擅长 | 短板 |
|--------|------|------|
| 关键词 | 精确 token、SKU、号码 | 同义改写 |
| 向量 | 语义、口语 | 稀有数字串 |

赵岩：「Day 30 让公告秒进库，今天让库**答得准**。」

下午 Lab 第三节，林晓跑 `hybrid_demo.py`，同一问句三列输出：vector 偏语义、keyword 命中号码、hybrid 把号码 chunk 顶到第一。全班盯着 `fusion=rrf` 与 `weighted` 的分差讨论——周航说：「RRF 不吵架，各看排名。」

第四节高潮：她 `PUT /api/knowledge/retrieval-config` 把 fusion 改成 `rrf`，再 `POST /api/chat`，客服场景立刻好转。陈默：「检索不是越新越好，是**两条腿走路**。」

```mermaid
journey
    title Day 31
    section 上午
      三模式对比: 5: 林晓
      RRF 公式白板: 4: 陈默
    section 下午
      hybrid_demo 三列: 5: 林晓
      API 切 fusion: 4: 林晓
      17 tests green: 5: 周航
```

**金句**：陈默：「向量懂意思，关键词认号码；融合不是妥协，是工程上的成年人选择。」

---

## 技术旁白：pool 为何是 top_k×4

`HybridRetriever.search` 在 hybrid 模式先各取 `pool = max(top_k * 4, 8)` 条候选，再融合截断到 `top_k`。池子太小会漏掉「一路排前、一路排后」的互补块；太大则浪费。8 是教学库的下限保底。

---

## 现场对话（转写节选）

**学员**：能否永远 keyword_weight=1？  
**陈默**：可以 `mode=keyword`，但「年化收益怎么样」类问句会掉召回。hybrid 是默认平衡点。

**学员**：RRF 的 k 是什么？  
**陈默**：`rrf_k=60` 是经典默认，越大排名靠后的贡献越平滑。

---

## 林晓日记节选

「昨天还在纠结 reset 几次，今天纠结 fusion 用 weighted 还是 rrf。原来检索质量是另一条战线。」

---

## 时间线

| 时刻 | 事件 |
|------|------|
| 09:00 | 复现手机号 vector miss |
| 10:30 | 讲 RetrievalConfig |
| 11:00 | **RRF 白板推导** |
| 14:00 | hybrid_demo 三模式 |
| 15:00 | API retrieval-config |
| 16:30 | 17 tests green |

---

## 媒体稿（公关）

智链 NexusAgent {VER} 上线混合检索，FAQ 对精确产品编号与客户电话的命中率显著提升，同时保持口语化咨询的语义理解能力。

---

## 幕后：教研组会议纪要

**议题**：默认 weighted 还是 rrf？  
**结论**：weighted 0.35/0.65 与历史向量偏好一致；文档推荐 SKU 场景试 RRF。  
**行动**：Day31 课件 Lab4 强制对比两种 fusion。

---

## 学员反馈（试讲）

「终于理解为什么客服爱贴号码 —— 那是 keyword 腿的主场。」  
「RRF 公式比想象中简单，难在理解 pool。」

---

## 彩蛋：电影隐喻

陈默：「向量像懂你在找什么感觉；关键词像认身份证号。破案要两个侦探合作。」
"""


def _file01() -> str:
    return f"""# Day 31 企业背景与今日任务

**需求**：{REQ} | **版本**：{VER}

## 背景

客服日报：37% 的「查电话 / 查 SKU」类工单，纯向量 top-1 未含目标 token。合规要求保留风险提示检索能力，不能一刀切 keyword。今日交付 **HybridRetriever** 与 **retrieval-config API**。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | HybridRetriever + RRF/加权 + RetrievalConfig |
| 下午 | Lab：三模式对比 + API 切 fusion + chat 验证 |
| 晚自习 | 读 Day 32 rerank 预习 |

## 自检

- [ ] 理解 KeywordRetriever vs ChromaEmbeddingRetriever  
- [ ] 能解释 `_normalize_scores` 的必要性  
- [ ] 读过 `02_需求文档.md` FR-003  

---

## 企业背景详述

智链理财知识库含产品说明书（语义长句）与页脚客服电话（精确数字）。单一向量模型对数字串 embedding 区分度不足；单一关键词对「收益怎么样」类口语弱。{REQ} 要求可配置三模式 + 两种融合。

---

## 相关方

| 角色 | 诉求 |
|------|------|
| 客服 | 电话/SKU 必中 |
| 产品 | 口语 FAQ 仍准 |
| 开发 | 可测可配 |
| 运维 | status 暴露 retrieval_config |

---

## 今日代码阅读顺序

1. `retrieval_config.py`（15 min）  
2. `hybrid_retriever.py`（45 min）  
3. `knowledge_store._build_rag_service`（15 min）  
4. `api/knowledge.py` retrieval-config（15 min）  
5. `tests/day31/`（30 min）  

---

## 成功画像

17:30 你能向客服主管解释：「为什么我们要 hybrid，以及何时切 RRF。」
"""


def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：知识库混合检索  
**优先级**：P0  
**平台版本**：{VER}

---

## 1. 背景

Day 29–30 完成 Chroma 向量检索与增量索引。生产反馈：精确 token 查询（手机号、SKU、条款编号）在纯向量模式下召回不足；纯关键词对口语化问句弱。需要可配置的 **keyword + vector 融合** 检索层。

## 2. 目标

- 提供 `vector` / `keyword` / `hybrid` 三模式  
- hybrid 支持 `weighted` 与 `rrf` 两种融合  
- 配置持久化并可经 REST 热更新  
- 默认 hybrid + weighted，兼顾语义与精确  

## 3. 功能需求

### FR-001 HybridRetriever 统一入口

- 类 `HybridRetriever` 实现与子检索器一致的 `search(query, top_k)`  
- 持有 `KeywordRetriever` 与 `ChromaEmbeddingRetriever`（或内存 `EmbeddingRetriever`）  
- `chunk_count` / `config` 属性可读  

### FR-002 单模式透传

- `mode=vector` → 仅调用向量腿  
- `mode=keyword` → 仅调用关键词腿  
- 空 query 或空 chunks → 返回 `[]`  

### FR-003 混合候选池与融合

- `mode=hybrid` 时 `pool = max(top_k * 4, 8)`  
- `fusion=weighted`：归一化两路分数后按权重求和  
- `fusion=rrf`：Reciprocal Rank Fusion，`score += 1/(rrf_k + rank)`  
- 融合后按 score 降序、`chunk.index` 次序截断 `top_k`  

### FR-004 RetrievalConfig 与校验

- 字段：`mode`, `keyword_weight`, `vector_weight`, `fusion`, `rrf_k`  
- `validate()` 拒绝非法 mode/fusion、非正权重和、rrf_k<1  
- `to_dict` / `from_dict` 往返  

### FR-005 持久化与 status

- `store.json` 存 `retrieval_config`  
- `GET /api/knowledge/status` 含 `retrieval_config`  
- `platform_version` 为 `{VER}`  

### FR-006 retrieval-config REST API

- `GET /api/knowledge/retrieval-config` 返回当前配置  
- `PUT /api/knowledge/retrieval-config` 更新并 `save()`  
- 非法 body → HTTP 422  

### FR-007 RAG 装配

- `_build_rag_service` 构造 `HybridRetriever` 注入 `DocumentIndex`  
- 配置变更后 `as_rag_service()` 使用新 config（缓存策略由 store 管理）  

### FR-008 演示与测试

- `day31/hybrid_demo.py` 对比三模式  
- `day31/hybrid_api_demo.py` 演示 API  
- `tests/day31/` 覆盖配置、融合、API、chat  

## 4. 非功能需求

### NFR-001 延迟

- hybrid 单次 `search` P95 < 200ms（教学库 <100 chunk，本地 Chroma）  
- 相对单模式，hybrid 开销 ≤ 2× 单腿延迟  

### NFR-002 可观测性

- status / retrieval-config 可读当前 mode 与 fusion  
- 演示脚本 stdout 可人工验收  

### NFR-003 兼容性

- 不破坏 Day 30 增量索引行为  
- 评估路径 `retrieval_eval` 仍可用内存检索器（不强制 hybrid）  

### NFR-004 可测试性

- `_rrf_merge` / `_weighted_merge` 可单测  
- API 测试使用 `TestClient` + 临时 store  

### NFR-005 安全

- retrieval-config 仅改检索策略，不暴露文件系统  
- 非法 mode 字符串拒绝，防注入式配置  

## 5. 非目标

- 学习型 rerank 模型（Day 32）  
- Query rewrite / HyDE  
- 多路召回（图片、表格独立索引）  
- Elasticsearch 后端  

---

## 5.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
| FR-001 | hybrid_retriever.HybridRetriever | test_hybrid_weighted_merge |
| FR-002 | HybridRetriever.search 分支 | test_hybrid_mode_vector_only |
| FR-003 | _weighted_merge / _rrf_merge | test_rrf_merge_helper |
| FR-004 | retrieval_config.py | test_retrieval_config_validate |
| FR-005 | knowledge_store save/load | test_knowledge_store_persists_retrieval_config |
| FR-006 | api/knowledge.py | test_put_retrieval_config_rrf |
| FR-007 | _build_rag_service | test_status_includes_retrieval_config |
| FR-008 | day31/* | test_health_version |

---

## 5.2 验收标准

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 默认 GET retrieval-config | mode=hybrid |
| AC-02 | PUT fusion=rrf | 200 且持久化 |
| AC-03 | 手机号 query hybrid | top-1 含号码或 keyword 腿命中 |
| AC-04 | mode=keyword | 不调用向量腿（行为等价） |
| AC-05 | chat 端到端 | 200 且 reply 非空 |

---

## 6. 详细验收步骤

### 6.1 单元测试

```bash
pytest tests/day31/test_hybrid_retriever.py -v
```

### 6.2 API 测试

```bash
pytest tests/day31/test_hybrid_api.py -v
```

### 6.3 演示

```bash
PYTHONPATH=src python3 src/day31/hybrid_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| 权重难调 | 提供 RRF 默认；文档给场景表 |
| hybrid 延迟翻倍 | pool 上限；教学库规模小 |
| 配置漂移 | store.json 持久化 + status 对账 |

---

## 8. 发布说明 {VER}

**新增**：HybridRetriever、RetrievalConfig、retrieval-config API  
**变更**：RAG 默认 hybrid 检索  
**注意**：切换 fusion 后建议抽样回归客服精确 query 集

---

## 9. NFR 验收命令

```bash
# NFR-004 可测试性
pytest tests/day31/ -q --tb=no

# NFR-001 延迟（本地粗测）
python3 -c "
import time
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
h = s.as_rag_service().index.retriever
t0=time.perf_counter()
h.search('年化收益', top_k=3)
print('ms', (time.perf_counter()-t0)*1000)
"
```

---

## 10. 需求变更记录

| 版本 | 变更 |
|------|------|
| v0.31.0-draft | 仅 weighted |
| v0.31.0 | 增加 RRF + API |

---

## 11. 开放问题（Phase 4）

- 是否学习权重？  
- 是否 query-dependent fusion？  
- 是否 BM25 替换 KeywordRetriever？  

---

## 12. PRD 签字页

产品：________  研发：________  测试：________  日期：2026-08-07
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求扩展 — 用户故事

## US-031-01 客服查电话

**作为** 客服坐席  
**我希望** 问「理财经理电话」或粘贴 11 位号码时 top-1 命中联系段落  
**以便** 减少转人工  

**验收**：`test_exact_phone_keyword_favors_hybrid` 绿；hybrid_demo 中号码 query keyword 列优于 vector。

## US-031-02 算法可切换

**作为** 算法工程师  
**我希望** 不重启服务即可 PUT fusion=rrf  
**以便** A/B 对比加权与 RRF  

**验收**：PUT 200；reload store 后配置仍在。

## US-031-03 合规保留语义 FAQ

**作为** 合规  
**我希望** 「投资有风险吗」仍走语义召回  
**以便** 风险提示不被纯 keyword 误伤  

**验收**：hybrid 模式下口语 query chat 200。

## US-031-04 运维可读

**作为** SRE  
**我希望** status 返回 retrieval_config  
**以便** 排障时知当前 mode  

---

## 边界：空库

`chunks` 为空时 `search` 返回 `[]`；`_build_rag_service` 返回空 `RAGContextService`。

## 与 Elasticsearch 类比

ES `bool` query 的 `should` 组合 BM25 与 kNN；本实现用 Python 层融合两路 `RetrievalResult` 列表，教学更清晰。

## 权重调参起点

| 场景 | keyword_weight | vector_weight |
|------|----------------|---------------|
| 客服电话/SKU 多 | 0.5–0.6 | 0.4–0.5 |
| 口语 FAQ 多 | 0.2–0.35 | 0.65–0.8 |
| 不确定 | — | — 用 RRF |

---

## US-031-05 审计

**作为** 审计  
**我希望** 配置变更有 API 记录（教学版仅 store.json 时间戳）  
**以便** 追溯谁改了 fusion  

---

## 非功能：回归集

维护 20 条 query：10 条精确 + 10 条语义。每次发版跑 hybrid_demo 人工 spot check。
"""


def _architecture() -> str:
    return f"""# Day 31 架构设计 — 混合检索层

## 1. 检索栈分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> RAG[RAGContextService]
    RAG --> IDX[DocumentIndex]
    IDX --> HR[HybridRetriever]
    HR --> KW[KeywordRetriever]
    HR --> VEC[ChromaEmbeddingRetriever]
    CFG[RetrievalConfig] --> HR
    STORE[(store.json)] --> CFG
```

## 2. search 分流

```mermaid
flowchart TD
    Q[query] --> M{{mode?}}
    M -->|vector| V[vector.search]
    M -->|keyword| K[keyword.search]
    M -->|hybrid| P[pool = max top_k*4, 8]
    P --> K2[keyword.search pool]
    P --> V2[vector.search pool]
    K2 --> F{{fusion?}}
    V2 --> F
    F -->|weighted| W[_weighted_merge]
    F -->|rrf| R[_rrf_merge]
    W --> T[top_k truncate]
    R --> T
```

## 3. 配置生命周期

```mermaid
stateDiagram-v2
    [*] --> hybrid_weighted: bootstrap default
    hybrid_weighted --> hybrid_rrf: PUT fusion=rrf
    hybrid_rrf --> keyword_only: PUT mode=keyword
    keyword_only --> vector_only: PUT mode=vector
    vector_only --> hybrid_weighted: PUT mode=hybrid
    hybrid_weighted --> hybrid_weighted: save store.json
```

## 4. 组件职责

| 组件 | 职责 |
|------|------|
| hybrid_retriever.py | 三模式 search + 融合函数 |
| retrieval_config.py | 配置 dataclass + validate |
| knowledge_store._build_rag_service | 装配双检索器 |
| api/knowledge retrieval-config | REST 读写配置 |
| day31/hybrid_demo.py | CLI 三模式对比 |

## 5. 不变量

- 任意模式返回 `list[RetrievalResult]`，元素含 `chunk` / `score` / `matched_tokens`  
- hybrid 融合后 score 仅用于排序，不跨请求比较绝对值（RRF 已归一化到 max）  

---

## 6. 与 Day30 增量正交

```mermaid
flowchart LR
    UP[upload incremental] --> CHUNKS[chunks + chroma]
    CHUNKS --> HR[HybridRetriever read path]
    CFG[retrieval_config] --> HR
```

写入路径不变；读取路径新增融合层。

---

## 7. 数据流：PUT retrieval-config

1. `RetrievalConfig.from_dict(body)`  
2. `validate()`  
3. `store.set_retrieval_config(cfg)`  
4. `store.save()`  
5. 下次 `as_rag_service()` 读新 config  

---

## 8. 并发模型（讨论）

多 worker 同时 PUT 配置可能 last-write-wins。教学单进程；生产可加乐观锁版本号。

---

## 9. 分层架构图

```
┌─────────────────────────────────────────────┐
│ Presentation: GET/PUT retrieval-config       │
├─────────────────────────────────────────────┤
│ Application: KnowledgeStore.get/set config   │
├─────────────────────────────────────────────┤
│ Domain: HybridRetriever.search               │
├─────────────────────────────────────────────┤
│ Infrastructure: Keyword + Chroma retrievers  │
└─────────────────────────────────────────────┘
```
"""


def _file04() -> str:
    from course_diagrams import file04

    return file04(31)


def _file05() -> str:
    return f"""# Day 31 课堂笔记（上午）

**09:00–09:40** 第一节：为何混合检索  
**09:40–10:30** 第二节：RetrievalConfig  
**10:30–11:20** 第三节：HybridRetriever.search 走读  
**11:20–12:00** 第四节：RRF 公式与加权归一化  

---

## 第一节：投诉案例（40 min）

纯向量对 `13900001111` top-1 miss。根因：数字串 embedding 区分度低 + 语义近邻抢占。

对比表：

| 模式 | 手机号 query | 口语 query |
|------|--------------|------------|
| vector | 易 miss | 强 |
| keyword | 强 | 中 |
| hybrid | **稳** | 强 |

---

## 第二节：RetrievalConfig（50 min）

{fenced("python", RETRIEVAL_CONFIG)}

要点：

- 默认 `MODE_HYBRID` + `FUSION_WEIGHTED` + 0.35/0.65  
- `validate()` 在 API PUT 前调用  
- `from_dict` 容忍缺失字段用默认  

**10:15** 课堂练习：写出非法 config 三组，预测 validate 异常信息。

---

## 第三节：search 分支（50 min）

{fenced("python", _HYBRID_SEARCH)}

**10:55** 板书：`pool = max(top_k * 4, 8)` — 为何 4 倍？互补召回需要足够候选。

单模式早返回：避免无谓双路开销。

---

## 第四节：RRF 白板（40 min）

对 rank=1 的文档：贡献 `1/(60+1)`。两路都排前则分数叠加。

对比 weighted：必须先 `_normalize_scores` 把每路 max 缩放到 1。

```python
# 11:10 板书
score_rrf(d) = Σ 1/(k + rank_i(d))
```

**11:40** 提问：RRF 为何不怕一路分数整体偏小？→ 只看排名。

---

## 第五节：_build_rag_service（20 min）

{fenced("python", _BUILD_RAG)}

装配顺序：EmbeddingClient load_state → sync chroma → vector → keyword → HybridRetriever。

**11:55** 强调：评估路径仍可用内存 retriever；生产 chat 走 hybrid。
"""


def _file06() -> str:
    return f"""# Day 31 课堂笔记（下午）

**14:00–14:30** 第五节：hybrid_demo 现场  
**14:30–15:20** 第六节：加权 merge 源码  
**15:20–16:00** 第七节：retrieval-config API  
**16:00–16:45** 第八节：pytest + chat 回归  

---

## 第五节：demo 三列（30 min）

```bash
PYTHONPATH=src python3 src/day31/hybrid_demo.py
```

记录 `HYBRID_QUERIES` 三条在各 mode 的 top-1 source。

**14:25** 学员汇报：号码 query vector 列是否 miss。

---

## 第六节：_weighted_merge（50 min）

{fenced("python", _WEIGHTED_MERGE)}

**14:50** 讲 `by_id.setdefault`：向量腿带来 keyword 未覆盖的 chunk。

**15:05** `combined <= 0` 跳过：两路都未命中则不出现在结果。

---

## 第七节：API（40 min）

{fenced("python", _RETRIEVAL_API)}

**15:35** curl 练习：

```bash
curl -s localhost:8000/api/knowledge/retrieval-config | jq .
curl -s -X PUT localhost:8000/api/knowledge/retrieval-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"mode":"hybrid","fusion":"rrf","rrf_k":60}}' | jq .
```

---

## 第八节：测试与 chat（45 min）

```bash
pytest tests/day31/ -v
```

**16:30** 里程碑：17 passed。

**16:40** `test_chat_with_hybrid_retrieval` 说明端到端未 mock 检索层。

---

## 故障表

| 现象 | 原因 | 处理 |
|------|------|------|
| hybrid 与 vector 相同 | pool 太小或权重极端 | 调 pool/权重 |
| PUT 422 | mode 拼写错 | 查 validate |
| 配置不持久 | 未 save | 查 store.json |
"""


def _file07() -> str:
    return f"""# Day 31 晚自习

## 讨论（19:00–19:45）

1. 为何 RRF 不需要 `_normalize_scores`？  
2. `keyword_weight=0.65, vector_weight=0.65` 合法吗？和不必为 1 的关系？  
3. 若上线 BM25，融合层要改吗？  

## 阅读（19:45–20:30）

`13_深度扩展_检索融合方法论.md`

## 预习 Day 32（20:30–21:00）

Cross-encoder rerank：在 hybrid top-N 上用更贵模型重排。

---

## 深度讨论：RRF 参数敏感性

| rrf_k | 效果 |
|-------|------|
| 10 | 头部排名权重更集中 |
| 60 | 经典默认，平滑 |
| 200 | 长尾排名也有贡献 |

---

## 晚自习物料：手写融合伪代码

```
kw = keyword.search(q, pool)
vec = vector.search(q, pool)
if fusion == rrf:
    return rrf_merge(kw, vec, k=60)[:top_k]
else:
    return weighted_merge(kw, vec, wk, wv)[:top_k]
```

---

## 自查清单

- [ ] 能默写三 mode 分支  
- [ ] 能解释 pool 公式  
- [ ] 跑通 hybrid_api_demo  
- [ ] 读过 22 精读第一节  

---

## 专题写作（选修 21:00–22:00）

用 200 字对比 Day29 纯向量、Day31 hybrid 在「13900001111」query 上的差异。要求提及 pool 与 fusion。

---

## 参考阅读页码

| 文档 | 章节 |
|------|------|
| 11_混合检索详解 | §3 RRF |
| 22_hybrid_retriever精读 | §四 search |
| 23_RRF与加权融合实践 | 实验 1–3 |

---

## 明日带物

笔记本电脑已装 pytest；能访问 nexus-agent-platform 仓库；预习 `27_Day32预习.md`。
"""


def _file08() -> str:
    return f"""# Day 31 作业

## A（35 分）：fusion 对比脚本

编写 `scripts/compare_fusion.py`：对 `HYBRID_QUERIES` 每条 query 打印 weighted vs rrf 的 top-1 `chunk_id` 是否一致。

**评分**：可运行 20 分；表格输出 10 分；简短结论 5 分。

## B（25 分）：问答

1. 写出 RRF 对 rank=1、rank=3 单路贡献（k=60）。  
2. 为何 weighted 要 `_normalize_scores`？  
3. `mode=hybrid` 但 `keyword_weight=1, vector_weight=0` 与 `mode=keyword` 行为差异？  

## C（25 分）：Lab 报告

完成 `26_实操Lab手册.md` Lab 0–7，含 Lab 4 融合对比截图。

## D（15 分）：配置审计

读取 `store.json` 的 `retrieval_config`，输出人类可读摘要（mode/fusion/权重）。

## E（bonus 10 分）：单元测试

为 `_normalize_scores` 空列表分支写测试 `test_normalize_scores_empty`。

## F（课堂参与 10 分，教师评）

知识竞赛或 demo 现场讲解 1 分钟：「何时选 RRF」。

---

## 学术诚信

允许讨论融合公式；禁止抄同伴 Lab 输出表格。

---

## 提交清单

- [ ] homework/day31-<姓名> 分支  
- [ ] lab/day31-姓名.md  
- [ ] 脚本 A（可选 E）  

## 提交

分支 `homework/day31-<姓名>`，截止次周上课前。

---

## 作业 A 参考骨架

```python
#!/usr/bin/env python3
from day31.constants import HYBRID_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, FUSION_WEIGHTED, MODE_HYBRID

store = KnowledgeStore.bootstrap_from_sample_docs()
for item in HYBRID_QUERIES:
    q = item["query"]
    for fusion in (FUSION_WEIGHTED, FUSION_RRF):
        store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=fusion))
        h = store.as_rag_service().index.retriever
        top = h.search(q, top_k=1)[0].chunk.chunk_id
        print(q, fusion, top)
```

---

## 评分细则

| 项 | 分 |
|----|-----|
| A 脚本 | 35 |
| B 问答 | 25 |
| C Lab | 25 |
| D 审计 | 15 |
| E bonus | +10 |
| F 参与 | 10 |
| 代码风格 | 5 |

---

## 作业 B 扩展题（讲师选用）

**B4（5分）** 画出 hybrid search 的 mermaid flowchart。  
**B5（5分）** 列举 validate 会拒绝的 3 种配置。

---

## 作业 C 详细 Rubric

| Lab | 必含元素 | 分值 |
|-----|----------|------|
| Lab4 | 三行对比表 | 15 |
| Lab5 | API 截图 | 5 |
| Lab7 | pytest 输出 | 5 |

---

## 作业 F 评分标准

| 表现 | 分 |
|------|-----|
| 清晰解释 RRF 适用场景 | 10 |
| 仅能背诵定义 | 5 |
| 未参与 | 0 |

---

## 历史优秀作业摘录（ anonymized ）

「号码 query 在 weighted 0.35/0.65 下已能 hit，但 RRF 在两条腿排名分散时更稳 — 我们的表第 2 行证明了这一点。」
"""


def _file09() -> str:
    return f"""# Day 31 作业答案

## B 参考答案

1. rank=1 → 1/61 ≈ 0.0164；rank=3 → 1/63 ≈ 0.0159  
2. 两路分数量纲不同，max 归一化后可加权  
3. hybrid 仍双路召回再融合；keyword 模式只跑 keyword 腿，省向量开销  

## A 参考要点

weighted 与 rrf 在口语 query 上常一致；精确号码 query 在 rrf 下可能更稳。

## D 参考

```python
cfg = raw.get("retrieval_config", {{}})
print(cfg.get("mode"), cfg.get("fusion"), cfg.get("keyword_weight"))
```

---

## C 报告评分表

| 项 | 优秀 | 及格 |
|----|------|------|
| Lab4 对比 | 三 query 全表 | 缺 1 条 |
| Lab7 chat | 截图 + 状态码 | 仅文字 |
| 三问 | 全对 | 对 2 问 |

---

## E 题答案要点

```python
def test_normalize_scores_empty():
    from rag.hybrid_retriever import _normalize_scores
    assert _normalize_scores([]) == {{}}
```

---

## 阅卷注意事项

- B 题 RRF 计算缺 k 扣 5 分  
- C 未贴 fusion 切换截图扣 10 分  
- F 需有课堂记录
"""


def _file10() -> str:
    return f"""# Day 31 混合检索验收清单

- [ ] `HybridRetriever` 三模式  
- [ ] `_weighted_merge` / `_rrf_merge`  
- [ ] `RetrievalConfig.validate`  
- [ ] `store.json` 持久化 retrieval_config  
- [ ] GET/PUT `/api/knowledge/retrieval-config`  
- [ ] `_build_rag_service` 装配 hybrid  
- [ ] `tests/day31/` 17 项全绿  
- [ ] `hybrid_demo.py` ✅  
- [ ] `hybrid_api_demo.py` ✅  
- [ ] status 含 retrieval_config  

**签字**：___________

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day31/ -q
python3 src/day31/hybrid_demo.py | grep -q "✅"
python3 src/day31/hybrid_api_demo.py | grep -q "✅"
echo DAY31_OK
```

---

## 精确 query 专项验收

- [ ] query `13900001111` hybrid top-1 含号码  
- [ ] query `年化收益率可达` 三模式均有命中  
- [ ] PUT fusion=rrf 后 GET 一致  

---

## 失败处置

| 失败 | 动作 |
|------|------|
| vector-only 无命中 | 查 chroma sync |
| PUT 422 | 查 body mode |
| 配置丢失 | 查 save() |

---

## 学员能力达成（ABCD）

A：能配置 retrieval-config  
B：能解释 RRF vs weighted  
C：能跑通 Lab 4 融合对比  
D：能教他人读 hybrid_demo 三列  
"""


def _file11() -> str:
    return f"""# 混合检索详解（Day 31 专题）

## 1. 问题定义

混合检索 = 在同一份 chunk 索引上，并行（或择一）执行稀疏与稠密召回，再融合排序。

## 2. 三模式对照

| mode | 行为 | 适用 |
|------|------|------|
| vector | 仅 cosine 相似度 | 探索、语义 FAQ |
| keyword | 仅 token 匹配 | 审计、精确编号 |
| hybrid | 双路 + 融合 | **生产默认** |

## 3. 融合算法

### 3.1 Weighted（默认）

```mermaid
flowchart LR
    KW[keyword hits] --> N1[normalize max=1]
    VEC[vector hits] --> N2[normalize max=1]
    N1 --> SUM["kw_w*ks + vec_w*vs"]
    N2 --> SUM
    SUM --> SORT[sort desc]
```

公式：`combined(d) = w_k * norm_k(d) + w_v * norm_v(d)`

默认 `w_k=0.35, w_v=0.65` 略偏语义，因口语 query 占比高。

### 3.2 RRF

```mermaid
flowchart TD
    R1[rank in keyword list] --> ADD["+= 1/(k+rank)"]
    R2[rank in vector list] --> ADD
    ADD --> NORM[divide by max score]
    NORM --> SORT[sort desc]
```

**优点**：不依赖分数标定；一路 BM25 式大分、一路 cosine 小分也能融合。  
**缺点**：丢失绝对置信度；tie-break 靠 `chunk.index`。

### 3.3 选型指南

| 信号 | 建议 |
|------|------|
| 两路分数尺度未知 | RRF |
| 有离线评估可标权重 | weighted |
| 精确 query 占比 >40% | 提高 keyword_weight 或 RRF |

## 4. 候选池 pool

`pool = max(top_k * 4, 8)`

**直觉**：若某 chunk 在 keyword 路排第 2、vector 路排第 20，pool 至少 20 才能进融合。4× 是经验系数；8 防止 top_k=1 时 pool=4 过小。

## 5. matched_tokens 合并

RRF 合并时保留 keyword 的 matched_tokens，并追加 vector 腿 token（去重）。便于 debug「为何这条排前」。

## 6. 与 Day30 关系

增量索引更新 chunk 与向量；HybridRetriever **只读** chunks 与 config，不改索引。

## 7. 常见误区

| 误区 | 正解 |
|------|------|
| hybrid = 平均两路原始分 | 须归一化或 RRF |
| RRF 的 k 越大越好 | 过大则排名区分度下降 |
| mode=hybrid 必比 vector 好 | 极端权重或坏库仍会失败 |

## 8. 数学例题

keyword 路：A rank1 score 100，B rank2 score 10。vector 路：B rank1 score 0.9，A 未进 top。`rrf_k=60`，问融合后谁前？

A: 1/61 ≈ 0.0164；B: 1/62 + 1/61 ≈ 0.0325 → **B 胜**。

## 9. 课堂演示

运行 hybrid_demo，对比 `13900001111` 三列。

## 10. 小结

混合检索三层含义：**双路召回**（互补）、**分数融合**（可比）、**可配置**（运营可调）。

---

## 11. 工作负载

设 pool=P，keyword 与 vector 各 O(P) 检索 + O(P) 融合 → hybrid ≈ 2× 单路。NFR-001 要求 P95 < 200ms。

---

## 12. RetrievalConfig JSON 示例

```json
{{
  "mode": "hybrid",
  "keyword_weight": 0.35,
  "vector_weight": 0.65,
  "fusion": "weighted",
  "rrf_k": 60
}}
```

---

## 13. 白板证明：为何号码偏 keyword

数字串在 TF-IDF / bag-of-token 中具唯一性；embedding 空间中对「13900001111」与「13900002222」距离可能很近 → vector 腿不稳定。

---

## 14. 端到端数值例题

top_k=3，pool=12。keyword 返回 8 条，vector 12 条，交集 5 条。问：融合结果最多几条？  
**答**：最多 15 条去重后再截 3。

---

## 15. 监控建议

- `hybrid_search_ms` histogram  
- `fusion_mode` gauge  
- 精确 query 集 hit@1 日报  

---

## 16. 与 Elasticsearch 混合检索对照

| ES | NexusAgent |
|----|------------|
| BM25 + dense_vector | Keyword + Chroma |
| RRF 插件 | _rrf_merge |
| 索引分离 | 同 chunk 双索引 |

---

## 17. 产品话术

「系统同时理解您话里的意思和您输入的精确编号，并智能合并两种搜索结果。」

---

## 18. 单元测试设计

- 测 helper：`_rrf_merge`、`_weighted_merge`  
- 测模式：vector/keyword 早返回  
- 测集成：store 持久化 config  

---

## 19. 反模式

在融合前对两路结果 **concat 去重不评分** — 丢失排序信息，hit@1 下降。

---

## 20. Phase 4 展望

引入 BM25 替换 KeywordRetriever；融合层接口不变。Day 32 rerank 在融合后再精排 top-20。

---

## 21. 完整 hybrid_retriever 源码（专题附录）

{fenced("python", HYBRID_RETRIEVER)}

---

## 22. weighted 数值走查例题

keyword 路：D1 score=8, D2 score=4。vector 路：D2 score=0.9, D3 score=0.3。权重 0.5/0.5。

归一化后：D1 kw=1, D2 kw=0.5, D2 vec=1, D3 vec=0.33。  
D2 combined=0.5×0.5+0.5×1=0.75 最高。

---

## 23. 课堂 10 分钟：何时切 keyword-only

临时活动仅查编号可 `mode=keyword`；活动结束务必恢复 hybrid。记录 incident 模板。

---

## 24. 与 query rewrite 边界

Rewrite 改 query 文本；fusion 改排序。Day32+ 可串联：rewrite → hybrid → rerank。

---

## 25. 监控大盘建议

- hit@1 按 query 类型分桶（精确/语义）  
- fusion 切换事件计数  
- hybrid P95 延迟  

---

## 26. 安全：检索模式泄露

status 暴露 mode 无敏感信息；勿在 retrieval-config 返回内部路径。

---

## 27. 批量评估伪代码

```python
for q in eval_queries:
    for mode in ("vector", "keyword", "hybrid"):
        hits = retriever.search(q, top_k=5)
        log_hit_at_k(q, mode, hits, gold)
```

---

## 28. 产品 FAQ 五条

**Q 混合检索是什么？** 同时用关键词和语义找资料再合并。  
**Q 默认模式？** hybrid。  
**Q 如何调？** PUT retrieval-config。  
**Q 会影响上传吗？** 不会，只影响查询。  
**Q 明天学什么？** rerank 精排。

---

## 29. 专题小结金句

「召回靠腿，融合靠脑；RRF 是排名民主，weighted 是分数加权民主。」
"""


def _file12() -> str:
    return f"""# Day 31 课堂练习册

## 一、选择题

**1.** 默认 fusion？ A rrf B weighted → B  
**2.** 默认 mode？ A vector B hybrid C keyword → B  
**3.** pool 公式？ A top_k*2 B max(top_k*4,8) C 固定10 → B  
**4.** RRF 用原始分？ A 是 B 否 → B  
**5.** validate 拒绝 rrf_k=0？ A 是 B 否 → A  

<details>
<summary>解析</summary>

1. `RetrievalConfig` 默认 `FUSION_WEIGHTED`。  
2. 生产默认 hybrid 平衡两路。  
3. 见 `HybridRetriever.search` 中 `pool = max(top_k * 4, 8)`。  
4. RRF 仅用排名。  
5. `rrf_k < 1` 抛 ValueError。
</details>

---

## 二、计算题

**6.** k=60，单路 rank=1 的 RRF 贡献？  

<details>
<summary>答案</summary>

1/(60+1) = 1/61 ≈ 0.01639
</details>

**7.** keyword_weight=0.4, vector_weight=0.6，两路 norm 均为 1，combined？  

<details>
<summary>答案</summary>

0.4×1 + 0.6×1 = 1.0
</details>

---

## 三、简答题

**8.** 解释为何精确手机号 query 在 vector 模式易失败。

<details>
<summary>参考答案</summary>

数字串 embedding 区分度不足；语义近邻 chunk（如风险提示）cosine 更高，挤占 top-k。
</details>

**9.** weighted 与 rrf 各适合什么团队阶段？

<details>
<summary>参考答案</summary>

weighted：有离线评估可标权重；rrf：快速上线、两路分数尺度不一。
</details>

---

## 四、代码阅读

**10.** 阅读 `_rrf_merge`，说明 `max_rrf` 除法目的。

<details>
<summary>答案</summary>

将 RRF 分缩放到 (0,1] 区间，便于与 weighted 路径一样用 score 字段展示，且 max 为 1。
</details>

---

## 五、实操

**11.** 运行 `hybrid_demo.py`，记录「投资有风险」在 hybrid 的 top-1 score。

<details>
<summary>提示</summary>

`PYTHONPATH=src python3 src/day31/hybrid_demo.py`，看 hybrid 列括号内分数。
</details>

---

## 六、判断题

**12.** mode=vector 时仍调用 keyword.search。×  
**13.** PUT retrieval-config 会触发 save。√  
**14.** hybrid 融合后 matched_tokens 可能为空。√  
**15.** pool 随 top_k 线性放大。√  

<details>
<summary>解析</summary>

12. vector 模式早返回，不调 keyword。  
13. `update_retrieval_config` 内 `store.save()`。  
14. vector 腿可能无 matched_tokens。  
15. pool = top_k * 4（下限 8）。
</details>

---

## 七、连线题

| 左 | 右 |
|----|-----|
| _normalize_scores | A. 排名融合 |
| _rrf_merge | B. max 归一化 |
| RetrievalConfig | C. 持久化于 store.json |
| _build_rag_service | D. 装配 HybridRetriever |

<details>
<summary>答案</summary>

_normalize_scores-B；_rrf_merge-A；RetrievalConfig-C；_build_rag_service-D
</details>

---

## 八、编程题（加分）

**16.** 写 3 行代码将 fusion 切为 `rrf` 并对 `"年化收益率"` search top_k=1。

<details>
<summary>参考</summary>

```python
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, MODE_HYBRID
s = KnowledgeStore.bootstrap_from_sample_docs()
s.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF))
print(s.as_rag_service().index.retriever.search("年化收益率", top_k=1))
```
</details>

---

## 九、案例讨论

**17.** 若产品坚持 vector-only，请列举 2 个业务风险。

<details>
<summary>参考答案</summary>

精确 SKU/电话 miss 导致工单上升；合规号码查询失败引发投诉。
</details>
"""


def _file13() -> str:
    return f"""# 深度扩展：检索融合方法论

## 1. 融合在 RAG 栈中的位置

```
Query → [可选 Rewrite] → 多路 Recall → Fusion → [可选 Rerank] → Context
```

Day 31 覆盖 Recall（双路）+ Fusion；Day 32 补 Rerank。

## 2. 经典融合族谱

| 方法 | 需要分数 | 需要排名 | 本仓库 |
|------|----------|----------|--------|
| 线性加权 | ✓（归一化） | | _weighted_merge |
| RRF | | ✓ | _rrf_merge |
| CombSUM | ✓ | | 未实现 |
| Learned LTR | ✓✓ | | Phase 5 |

## 3. RRF 论文要点（Cormack et al.）

`RRF(d) = Σ 1/(k + r(d))`，k 常取 60。对多检索系统鲁棒，无需分数校准。

## 4. 权重学习（扩展）

若有标注 query-chunk 相关性，可用 grid search `keyword_weight` 最大化 hit@1。教学用手动表。

## 5. 负例：简单 concat

```python
# 反模式
return list({{*kw_hits, *vec_hits}})[:top_k]
```

丢失分数与排名，生产禁用。

## 6. 多语言与分词

Keyword 腿依赖 tokenize；中文需与 Day26 分词一致。向量腿对分词错误较鲁棒 → hybrid 另一收益。

## 7. 延迟优化方向

- 并行 keyword/vector search（线程池）  
- 缩小 pool  
- 缓存热 query 融合结果  

## 8. 安全：权重注入

PUT body 仅接受数值权重，拒绝 NaN/Inf（可在 validate 扩展）。

## 9. 与 ColBERT / 晚期交互对照

晚期交互在模型内融合；本课早期融合 + Day32 晚期 rerank 是渐进路径。

## 10. 阅读清单

- Cormack, Clarke, Buettcher: Reciprocal Rank Fusion  
- Lin et al.: BM25 与神经检索混合实践综述（概念）

---

## 11. 工业界融合案例简表

| 产品 | 策略 |
|------|------|
| Pinecone hybrid | dense + sparse |
| OpenSearch | BM25 + kNN RRF |
| NexusAgent D31 | Keyword + Chroma RRF/weighted |

---

## 12. 数学：加权融合凸组合讨论

当 `keyword_weight + vector_weight = 1` 且 norm∈[0,1] 时，combined∈[0,1]。不要求和为 1 时，combined 可>1，仍可按相对大小排序。

---

## 13. 实验设计：显著性检验

对比 fusion 策略需同一 query 集、同一 gold chunk；McNemar 检验 hit@1 差异（高级选修）。

---

## 14. 失败案例分析

某团队 vector_weight=0.95 导致 SKU query 回退 — 应用分 query 类型路由或 RRF。

---

## 15. 融合层单元测试清单

- [ ] 空 kw / 空 vec  
- [ ] 单 id 双路  
- [ ] 无交集双 id  
- [ ] 同分 tie index  

---

## 16. 部署检查单

- [ ] 默认 config 与 PRD 一致  
- [ ] PUT 权限控制（生产）  
- [ ] 回滚 weighted 预案  

---

## 17. 术语中英对照

| 中文 | EN |
|------|-----|
| 混合检索 | Hybrid Retrieval |
|  reciprocal rank fusion | RRF |
| 稀疏 | Sparse |
| 稠密 | Dense |

---

## 18. 深度阅读笔记模板

- 今日最大收获：  
- 仍困惑：  
- 想尝试的权重：  

---

## 19. 与 ColBERT 晚期交互

ColBERT 在 token 级交互；本课早期融合 + Day32 晚期 rerank 是更常见的工程阶梯。

---

## 20. 方法论结语

融合不是「拍脑袋平均」，而是**明确假设**：排名可移植（RRF）或归一化后线性可组合（weighted）。
"""


def _file14() -> str:
    return f"""# 企业案例集：精确 SKU 查询

## 案例 A：理财 SKU「ZL-FIX-2024-A」

**现象**：销售在 IM 粘贴 SKU，纯向量 top-1 返回「同类产品比较」段落。  
**根因**：SKU 字符在语料中出现次数少，embedding 与描述句相近。  
**处置**：切换 hybrid + keyword_weight=0.5，hit@1 从 41% → 89%。

## 案例 B：客服电话 13900001111

**现象**：与 Day31 课堂投诉相同。  
**数据**：vector hit@1 38%；keyword 92%；hybrid（RRF）94%。  
**话术**：培训坐席可粘贴完整号码查询。

## 案例 C：条款编号「第3.2.1条」

keyword 腿对「3.2.1」token 敏感；vector 对「违约金」语义敏感。hybrid 在「第3.2.1条违约金」合成 query 上优于单路。

## 案例 D：误切 keyword-only

运营为救 SKU 将 mode=keyword，一周后口语 FAQ 满意度降 12%。回 hybrid + RRF 恢复。

## 案例 E：双11 大促 SKU 清单

200 个新 SKU 入库（Day30 增量），检索策略未改。hybrid 无需重训 embedding，仅依赖新 chunk 进索引 — 与增量正交验证。

---

## ROI 幻灯片

| 指标 | 向量 only | hybrid |
|------|-----------|--------|
| 精确 query hit@1 | 0.38 | 0.91 |
| 语义 query hit@1 | 0.84 | 0.86 |
| P95 延迟 ms | 95 | 168 |

---

## 客户邮件模板

主题：混合检索上线（{VER}）

正文：针对产品编号与联系电话类问题，系统已启用关键词与语义双路融合检索，预计精确类工单下降 30%。

---

## 案例 F：跨境 SKU 含字母与数字

SKU `ZL-2024-CN-09` 在 vector 路与「2024 年度报告」混淆；keyword 腿对完整 token 串敏感，hybrid RRF 将产品页顶至首位。

---

## 案例 G：批量导入后的检索回归

2000 SKU 经 Day30 增量入库后，无需重训向量模型；调节 `keyword_weight` 至 0.55 即通过 QA 回归。

---

## 案例 H：A/B 实验设计

对照组 vector-only 7 天 vs 实验组 hybrid 7 天；指标：精确 query 工单率、口语 FAQ CSAT、P95 延迟。实验组工单率 -28%，CSAT 持平，延迟 +18%。

---

## 案例 I：失败与回滚

一次误将 `mode=keyword` 写入生产 store.json，口语 FAQ 满意度降；15 分钟内 PUT 恢复 hybrid weighted，监控恢复。

---

## 案例 J：培训材料摘录

给客服的三句话：  
1. 查电话请粘贴完整号码。  
2. 问「怎么样」类问题保持自然语言即可。  
3. 系统已自动合并两种搜索，无需选模式。
"""


def _file15() -> str:
    return f"""# Day 31 授课实录

**09:02** 林晓投影客服工单，vector miss 复现。  
**09:18** 陈默画双路检索表。  
**10:05** RetrievalConfig  live coding validate。  
**10:48** 白板推 RRF 公式，学员跟算 1/61。  
**11:15** `_build_rag_service` 走读结束。  

**14:03** hybrid_demo 三列，学员惊呼号码列。  
**14:41** 讲 `_weighted_merge` 的 setdefault。  
**15:08** PUT retrieval-config 成功，status 对账。  
**15:52** pytest 第 15 个绿。  
**16:38** `test_chat_with_hybrid_retrieval` 通过。  
**16:55** 预告 Day32 rerank：「融合后还可再挑一遍」。  

---

## 问答实录

**15:22 学员**：hybrid 能否三路（加 BM25）？  
**陈默**：接口可扩展；本版两路够教学。BM25 换 keyword 腿即可。

**16:10 学员**：chat 用哪条 config？  
**林晓**：`get_knowledge_store().get_retrieval_config()` 每次 `as_rag_service` 读取。

---

## 讲师自评

- RRF 公式 45min 刚好  
- Lab4 融合对比是本周高光  
- 明日 rerank 衔接自然

---

## 时间戳逐字稿（节选）

**10:02:18** 陈默：「Reciprocal Rank Fusion，分子是 1，分母是 k 加 rank。」  
**10:03:05** 学员：「k 固定 60？」  
**10:03:12** 陈默：「教学默认 60，可调，但别小于 1。」  
**14:16:44** 林晓：（运行 demo）「大家看第三列 hybrid，号码上来了。」  
**15:33:01** 周航：「PUT 返回 200，fusion 字段已是 rrf。」  
**16:41:22** 全班：「17 passed！」  

---

## 设备与环境备注

投影延迟导致 demo 第一次 `as_rag_service` 较慢；第二次切换 mode 明显加快 — 可借机讲缓存与重建成本。

---

## 课后作业布置原话

「Lab4 表格必须手填，不许抄邻座。作业 A 的 fusion 对比脚本周五 23:59 前 push。」
"""


def _file16() -> str:
    return f"""# Day 31 复习卡片（20 张）

**Q1** 默认 mode？ → hybrid  
**Q2** 默认 fusion？ → weighted  
**Q3** 默认权重？ → 0.35 / 0.65  
**Q4** pool 公式？ → max(top_k*4, 8)  
**Q5** RRF 分母？ → rrf_k + rank  
**Q6** 默认 rrf_k？ → 60  
**Q7** 需求号？ → {REQ}  
**Q8** 平台版本？ → {VER}  
**Q9** 融合前 weighted 必做？ → _normalize_scores  
**Q10** 单模式 vector 调谁？ → self._vector.search  

**Q11** API 路径？ → /api/knowledge/retrieval-config  
**Q12** 装配函数？ → _build_rag_service  
**Q13** demo 脚本？ → hybrid_demo.py  
**Q14** 测试数？ → 17  
**Q15** 精确号码案例？ → 13900001111  

**Q16** FR-003 讲什么？ → 混合候选池与融合  
**Q17** validate 拒绝？ → 非法 mode/fusion、权重和≤0、rrf_k<1  
**Q18** RRF 用分数吗？ → 否，用排名  
**Q19** Day32 主题？ → rerank  
**Q20** 与 Day30 关系？ → 写入增量 vs 读取融合，正交  
"""


def _file17() -> str:
    return f"""# 混合检索 API 速查手册

## GET retrieval-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/retrieval-config | jq .
```

响应：

```json
{{
  "mode": "hybrid",
  "keyword_weight": 0.35,
  "vector_weight": 0.65,
  "fusion": "weighted",
  "rrf_k": 60
}}
```

## PUT retrieval-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/retrieval-config \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "mode": "hybrid",
    "fusion": "rrf",
    "keyword_weight": 0.4,
    "vector_weight": 0.6,
    "rrf_k": 60
  }}'
```

## status 中的 retrieval_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.retrieval_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, MODE_HYBRID

store = get_knowledge_store()
store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF))
store.save()
```

## 错误码

| 状态 | 原因 |
|------|------|
| 422 | mode/fusion 非法或 rrf_k<1 |
| 200 | 成功并持久化 |

## 常量

- `MODE_VECTOR` / `MODE_KEYWORD` / `MODE_HYBRID`  
- `FUSION_WEIGHTED` / `FUSION_RRF`  
"""


def _file18() -> str:
    return f"""# Day 31 与 Day 30 能力对照表

| 维度 | Day 30 增量索引 | Day 31 混合检索 |
|------|-----------------|-----------------|
| 需求 | ZL-NA-REQ-030 | {REQ} |
| 版本 | v0.30.0 | {VER} |
| 核心问题 | 上传慢、全量 reset | 精确 query miss |
| 核心模块 | _incremental_index | HybridRetriever |
| API 新增 | index_mode 字段 | retrieval-config |
| 存储字段 | last_incremental_at | retrieval_config |
| 测试目录 | tests/day30/ | tests/day31/ |
| demo | incremental_demo | hybrid_demo |
| 与检索关系 | 写路径 | 读路径 |
| 下一日 | Day31 混合 | Day32 rerank |

## 协同场景

1. Day30 上传新 SKU 文档（增量）  
2. Day31 hybrid 使 SKU query 命中  
3. 二者无代码冲突  

## 排障对照

| 症状 | 先查 Day | 关键字 |
|------|----------|--------|
| 上传慢 | 30 | vocab_expanded |
| 搜不到新文档 | 30 | incremental |
| 号码/SKU miss | 31 | mode, fusion |
| 口语 FAQ 差 | 31 | vector_weight |
| 配置丢失 | 31 | store.save |

---

## 能力叠加示意图

```
Day29 Chroma  ──┐
Day30 增量    ├──► Day31 Hybrid ──► Day32 Rerank
Day28 rebuild ──┘
```

---

## 迁移指南（Day30→31 发版）

1. 部署 {VER} 二进制/容器  
2. 首次启动自动 `RetrievalConfig()` 默认  
3. 跑 `pytest tests/day30 tests/day31`  
4. 抽样客服 query 回归  
5. 监控 hybrid P95  

---

## 对照测验（自测 10 题）

1. Day30 核心函数？ `_incremental_index`  
2. Day31 核心类？ `HybridRetriever`  
3. Day30 扩张触发？ vocab_expanded  
4. Day31 融合默认？ weighted  
5. Day30 API 字段？ index_mode  
6. Day31 API 路径？ retrieval-config  
7. 两者正交？ 是  
8. Day30 测试数？ 16  
9. Day31 测试数？ 17  
10. 下一日？ rerank  
"""


def _file19() -> str:
    return f"""# 讲师补充阅读

## 1. Reciprocal Rank Fusion 原文脉络

RRF 来自 IR 融合实验，核心洞察：**排名比分数更可移植**。可与学员讨论 k=60 的来源（经验稳定区间）。

## 2. Azure AI Search 混合检索

微软文档描述 vector + BM25 RRF — 与本案架构同构，可作企业参考。

## 3. Weaviate hybrid 参数 alpha

alpha=0 纯 BM25，alpha=1 纯向量，中间混合 — 类比本课 keyword_weight。

## 4. 课堂彩蛋：SimHash 去重

融合前去重相同 chunk_id 已做；扩展可对近重复 chunk 合并分数。

## 5. 伦理与合规

精确检索客服电话需权限控制；检索层不负责鉴权，API 网关须限制导出。

## 6. 推荐阅读顺序

1. hybrid_retriever.py  
2. Elasticsearch RRF blog（概念）  
3. Day32 rerank 预习  
"""


def _file20() -> str:
    return f"""# Day 31 完整代码走查

按**调用顺序**阅读，预计 90 分钟。精读全文见 `22_hybrid_retriever精读.md`。

---

## 走查路线

| 顺序 | 文件 | 关注 |
|------|------|------|
| 1 | `retrieval_config.py` | validate / defaults |
| 2 | `hybrid_retriever.py` | search + merge |
| 3 | `knowledge_store.py` | _build_rag_service |
| 4 | `api/knowledge.py` | retrieval-config |
| 5 | `day31/hybrid_demo.py` | 三模式 |
| 6 | `day31/hybrid_api_demo.py` | TestClient |
| 7 | `tests/day31/` | 17 项 |

---

## 1. 配置层

`RetrievalConfig` 是单一真相源。store 启动 `from_dict` 加载；API PUT 更新。

**检查点**：默认值与 PRD FR-004 一致。

---

## 2. search 调用栈

```
POST /api/chat
  → RAGContextService.retrieve
    → DocumentIndex.search
      → HybridRetriever.search
        → [vector|keyword|hybrid 分支]
```

---

## 3. _build_rag_service

{fenced("python", _BUILD_RAG)}

**练习**：在 keyword 与 vector 构造处打断点，确认 chunks 同源。

---

## 4. API 层

{fenced("python", _RETRIEVAL_API)}

**检查点**：422 来自 `ValueError` → HTTPException。

---

## 5. hybrid_demo

{fenced("python", HYBRID_DEMO)}

对每条 `HYBRID_QUERIES` 切换 mode 重建 retriever（经 `as_rag_service`）。

---

## 6. 测试矩阵

| 文件 | 覆盖 |
|------|------|
| test_hybrid_retriever.py | 模式、融合、持久化、helper |
| test_hybrid_api.py | HTTP、chat、version |

**必读**：`test_exact_phone_keyword_favors_hybrid`、`test_put_retrieval_config_rrf`。

---

## 7. 走查后自测

1. 闭卷写出 hybrid 路径 5 步。  
2. 说明 weighted 为何 normalize。  
3. 指出 PUT 后 chat 如何读到新 fusion。

---

## 8. knowledge_store 检索配置节选

{fenced("python", KNOWLEDGE_STORE[KNOWLEDGE_STORE.find("def get_retrieval_config"):KNOWLEDGE_STORE.find("def set_chunk_config")])}

---

## 9. 完整 hybrid_retriever（走查用）

{fenced("python", HYBRID_RETRIEVER)}

---

## 10. 走查时间盒（90 min 细分）

| 分钟 | 内容 |
|------|------|
| 0–15 | retrieval_config |
| 15–45 | hybrid_retriever |
| 45–60 | _build_rag_service + API |
| 60–75 | demos |
| 75–90 | tests |

---

## 11. 常见问题走查

**Q save 后 RAG 何时刷新？** `as_rag_service()` 重建或内部缓存失效时。  
**Q 评估为何不用 hybrid？** `retrieval_eval` 隔离变量，仅比 chunk_config。  

---

## 12. 走查验收 oral exam

学员随机抽：讲解 `_rrf_merge` 中 `max_rrf` 作用。
"""


def _file21() -> str:
    return f"""# Day 31 课堂知识竞赛（15 题）

1. 混合检索器类名？ → `HybridRetriever`  
2. 默认 fusion？ → `weighted`  
3. RRF 超参 k 字段名？ → `rrf_k`  
4. pool 下限？ → `8`  
5. 需求号？ → {REQ}  
6. 平台版本？ → {VER}  
7. retrieval-config HTTP 方法？ → GET + PUT  
8. 加权融合函数？ → `_weighted_merge`  
9. 排名融合函数？ → `_rrf_merge`  
10. 归一化函数？ → `_normalize_scores`  
11. 演示常量文件？ → `day31/constants.py`  
12. 测试总数？ → 17  
13. 精确号码样例？ → 13900001111  
14. FR-007 实现？ → `_build_rag_service`  
15. Day32 主题？ → rerank（交叉编码器重排）  

---

## 抢答加分题（讲师用）

**16** 写出 weighted combined 公式。  
**答**：`keyword_weight * norm_k + vector_weight * norm_v`

**17** hybrid 模式 vector 腿类型？  
**答**：`ChromaEmbeddingRetriever`（或评估时 `EmbeddingRetriever`）

---

## 决赛三轮（讲师用）

**18** 默写 pool 公式与 RRF 单项贡献公式。  
**19** 指出 `api/knowledge.py` 中 retrieval-config 两个路由 HTTP 方法。  
**20** 说明 `test_knowledge_store_persists_retrieval_config` 验证什么。

**答 19**：GET、PUT  
**答 20**：save/load 后 mode 与 fusion 不丢失

---

## 记分板模板

| 组 | 基础15题 | 决赛5题 | 总分 |
|----|----------|---------|------|
| A | | | |
| B | | | |

满分 20 题，每题 5 分。决赛题需写出关键公式额外 +2。

---

## 赛后复盘（教研组）

竞赛题 14（FR-007）正确率最低，说明 `_build_rag_service` 走查仍需加强。下节课前 5 分钟口头抽查装配顺序：EmbeddingClient → chroma → vector → keyword → HybridRetriever。

**附**：奖品为《信息检索导论》电子版书签一份，共 3 名。

**裁判**：陈默、林晓、周航各负责 5 题标准答案核对，争议由陈默终裁。
"""


def _file22() -> str:
    return f"""# Day 31 精读：hybrid_retriever 与融合层

**需求**：{REQ} | **学时**：120 min

---

## 一、hybrid_retriever.py 全文

{fenced("python", HYBRID_RETRIEVER)}

---

## 二、行级注释：模块头与导入（L1–L23）

| 行 | 代码 | 讲解 |
|----|------|------|
| L1–L8 | 模块 docstring | 声明 ZL-NA-REQ-031；点明 keyword+vector 融合目标 |
| L12–L13 | TextChunk / Chroma | 向量腿走 Chroma；chunk 元数据贯穿 RetrievalResult |
| L15–L22 | retrieval_config 常量 | 避免魔法字符串；与 API JSON 枚举一致 |
| L23 | KeywordRetriever | 稀疏腿；token 重叠 + TF 分数 |

---

## 三、行级注释：HybridRetriever 类（L26–L55）

| 行 | 讲解 |
|----|------|
| L36–L47 | 构造器注入双检索器 + 可选 config；默认 `RetrievalConfig()` |
| L49–L51 | `chunk_count` 代理 chunks 长度，供 status 展示 |
| L53–L55 | `config` 只读属性，测试中断言 fusion 切换 |

---

## 四、行级注释：search 主流程（L57–L80）

{fenced("python", _HYBRID_SEARCH)}

| 行 | 讲解 |
|----|------|
| L58–L60 | 空 query / 空库 → 早返回 `[]`，防无意义 Chroma 调用 |
| L63–L66 | **单模式早返回**：性能与语义清晰，不做假融合 |
| L68 | `pool = max(top_k * 4, 8)` 候选池 — **必读考点** |
| L69–L70 | 同 query、同 pool 各搜一路 |
| L71–L79 | fusion 二分；`merged[:max(1, top_k)]` 保证至少尝试返回 1 条（有结果时） |

---

## 五、_weighted_merge 全文与注释

{fenced("python", _WEIGHTED_MERGE)}

| 行 | 讲解 |
|----|------|
| L91–L92 | 分路 max 归一化 → [0,1]，消除 TF 与 cosine 量纲差 |
| L95–L98 | 并集 chunk_id；keyword 优先写入，vector `setdefault` 补新 id |
| L102–L104 | 加权求和；`combined<=0` 跳过两路都未有效打分的 id |
| L107 | matched_tokens 去重保序 |
| L115 | 次键 `chunk.index` 稳定排序 |

---

## 六、_rrf_merge 全文与注释

{fenced("python", _RRF_MERGE)}

| 行 | 讲解 |
|----|------|
| L130–L134 | keyword 路：按 rank 累加 `1/(rrf_k+rank)`，记 tokens |
| L136–L142 | vector 路：同公式累加；合并 matched_tokens |
| L144–L152 | 除以 `max_rrf` 归一化展示分；排序规则同 weighted |

**考点**：同一 chunk 两路都靠前 → RRF 分叠加 → hybrid 优势场景。

---

## 七、_normalize_scores

```python
def _normalize_scores(hits: list[RetrievalResult]) -> dict[str, float]:
    if not hits:
        return {{}}
    max_s = max(r.score for r in hits) or 1.0
    return {{r.chunk.chunk_id: r.score / max_s for r in hits}}
```

空列表返回 `{{}}` — 作业 E 考点。`or 1.0` 防全零除零。

---

## 八、retrieval_config.py 全文

{fenced("python", RETRIEVAL_CONFIG)}

`validate()` 在 hybrid 模式只要求权重和 >0，**不要**求和为 1 — 允许运营放大整体尺度。

---

## 九、_build_rag_service 装配

{fenced("python", _BUILD_RAG)}

HybridRetriever 成为 `DocumentIndex` 唯一 retriever；chat 无感知融合细节。

---

## 十、测试精读 test_hybrid_retriever.py

{fenced("python", TEST_HYBRID)}

| 测试 | 要点 |
|------|------|
| test_retrieval_config_validate | 非法 mode 抛错 |
| test_hybrid_mode_vector_only | 早返回向量腿 |
| test_hybrid_weighted_merge | score>0 |
| test_hybrid_rrf_merge | RRF 路径 smoke |
| test_exact_phone_keyword_favors_hybrid | **业务金测** |
| test_rrf_merge_helper | 纯函数 2 条合并 |
| test_weighted_merge_helper | 同 id 双路 |

---

## 十一、API 测试 test_hybrid_api.py

{fenced("python", TEST_HYBRID_API)}

`test_health_version` 锁版本 `{VER}`；`test_chat_with_hybrid_retrieval` 端到端。

---

## 十二、调试清单

- [ ] 打印 kw_hits / vec_hits 各前 5  
- [ ] 打印 fusion 后前 3 score  
- [ ] 切换 mode 对比是否早返回  
- [ ] 查 store.json retrieval_config  

---

## 十三、自检

1. 手绘 hybrid search 流程图。  
2. 口述 RRF 对 rank=1 的贡献。  
3. 说明为何 weighted 必须 normalize。

---

## 十四、笔试模拟

**1（20分）** 证明：当 keyword 路与 vector 路 top-1 不同 id 时，RRF 可能使「两路都排前5」的 id 胜出。

**2（20分）** 解释 `pool` 过小导致融合失效的反例。

**3（20分）** 对比 FR-002 与 FR-003 的实现位置。

---

## 十五、与 Day30 衔接

增量更新 chunk 后，HybridRetriever 持有新 chunks 引用；**无需**为混合检索单独 rebuild。若 TF-IDF 扩张 reset，两路索引同时更新。

---

## 十六、完整 knowledge_store 交叉引用（节选）

{fenced("python", KNOWLEDGE_STORE[KNOWLEDGE_STORE.find("def get_retrieval_config"):KNOWLEDGE_STORE.find("def ingest_bytes")])}

`set_retrieval_config` 深拷贝 `from_dict(to_dict())` 防别名突变。

---

## 十七、口语考试题

1. 30 秒解释 hybrid 是什么。  
2. 1 分钟对比 weighted vs RRF。  
3. 白板画 search 分支。

---

## 十八、实验记录模板

| query | mode | fusion | top1_id | top1_score |
|-------|------|--------|---------|------------|
| | | | | |

---

## 十九、FAQ

**Q 能否 async 并行两路？** 可优化；当前同步教学实现。  
**Q matched_tokens 空？** vector 腿常为空，正常。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `HybridRetriever.search` 与两种 merge 函数，并映射到 {REQ} 的 FR-001–FR-003。

---

## 二十一、hybrid_retriever 完整源码（重复嵌入便于打印）

{fenced("python", HYBRID_RETRIEVER)}

---

## 二十二、融合函数对照伪代码

```
function HYBRID_SEARCH(q, top_k):
    if mode == vector: return VEC(q, top_k)
    if mode == keyword: return KW(q, top_k)
    P = max(top_k * 4, 8)
    a = KW(q, P)
    b = VEC(q, P)
    if fusion == rrf: return RRF(a, b)[:top_k]
    return WEIGHTED(a, b)[:top_k]
```

---

## 二十三、HYBRID_QUERIES 业务解读

| query | 业务意图 | keyword 腿 | vector 腿 |
|-------|----------|------------|-----------|
| 年化收益率可达 | 产品收益 FAQ | 命中「年化」「8%」 | 语义近邻 |
| 13900001111 | 查电话 | **强命中号码** | 易漂移到风险段 |
| 投资有风险 | 合规披露 | 「风险」token | 语义概括 |

---

## 二十四、测试与 FR 映射（完整）

| 测试 | FR/NFR |
|------|--------|
| test_retrieval_config_validate | FR-004 |
| test_hybrid_mode_vector_only | FR-002 |
| test_hybrid_mode_keyword_only | FR-002 |
| test_hybrid_weighted_merge | FR-003 |
| test_hybrid_rrf_merge | FR-003 |
| test_exact_phone_keyword_favors_hybrid | AC-03 |
| test_knowledge_store_persists_retrieval_config | FR-005 |
| test_status_includes_retrieval_config | FR-005 |
| test_rrf_merge_helper | FR-003 |
| test_weighted_merge_helper | FR-003 |
| test_health_version | FR-008 |
| test_get_retrieval_config_default_hybrid | AC-01 |
| test_put_retrieval_config_rrf | AC-02 |
| test_invalid_retrieval_mode_422 | FR-006 |
| test_chat_with_hybrid_retrieval | AC-05 |
| test_switch_to_keyword_mode | FR-002 |

---

## 二十五、knowledge API 全文（检索相关上下文）

{fenced("python", KNOWLEDGE_API[:8000])}

---

## 二十六、phase3_hybrid_review 建议

课后运行 `src/day31/phase3_hybrid_review.py`（若存在）串联 Day25–31 概念。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| RRF 用原始分 | 用 rank |
| hybrid 一定优于 vector | 取决于 query 与权重 |
| PUT 不 save | API 内 save |

---

## 二十八、50 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 RRF 公式  
3. 能解释 normalize  
4. 能定位 _build_rag_service  
5. 能 curl GET retrieval-config  
6. 能 curl PUT rrf  
7. 能跑 hybrid_demo  
8. 能跑 hybrid_api_demo  
9. 能数清 17 tests  
10. 能解释 13900001111 案例  
11. 能对比 Day30 正交  
12. 能预告 Day32 rerank  
13. 能读 validate 源码  
14. 能读 setdefault 语义  
15. 能解释 matched_tokens  
16. 能解释 chunk.index tie-break  
17. 能解释 MODE_* 常量  
18. 能解释 FUSION_* 常量  
19. 能解释 platform_version  
20. 能复述 {REQ} 目标  

---

## 二十九、延伸阅读：Retriever 接口

KeywordRetriever 与 ChromaEmbeddingRetriever 均实现 `search(query, top_k)` → `list[RetrievalResult]`。HybridRetriever 是 **Decorator / Facade** 模式，统一对外接口。

---

## 三十、完整测试文件（API）

{fenced("python", TEST_HYBRID_API)}

---

## 三十一、课堂录音稿（8 min）

「打开 hybrid_retriever，找到 search。先看两个 if：vector、keyword 单腿。然后 pool。记住四倍与八。fusion 分支：weighted 先 normalize 再加权；rrf 只看排名。最后截断 top_k。这就是 ZL-NA-REQ-031 的全部读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): hybrid retrieval with RRF/weighted fusion (ZL-NA-REQ-031)

- HybridRetriever + RetrievalConfig
- GET/PUT /api/knowledge/retrieval-config
- tests/day31 (17 cases)
```

---

## 三十三、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 31 · 混合检索 · {REQ} · hybrid_retriever 精读完**
"""


def _file23() -> str:
    return f"""# RRF 与加权融合实践

## 实验 1：手工 RRF 计算

设 `rrf_k=60`。

| doc | keyword rank | vector rank | RRF 分 |
|-----|--------------|-------------|--------|
| A | 1 | - | 1/61 |
| B | 3 | 1 | 1/63+1/61 |
| C | - | 2 | 1/62 |

排序 B > C > A（可课堂验算）。

## 实验 2：weighted 权重扫描

```python
for kw in (0.2, 0.35, 0.5, 0.7):
    cfg = RetrievalConfig(mode="hybrid", fusion="weighted",
                          keyword_weight=kw, vector_weight=1-kw)
    # 对 HYBRID_QUERIES 打 hit@1
```

记录：号码 query 在 kw≥0.5 时 hit@1 提升。

## 实验 3：fusion A/B

同库同样 query，对比 weighted 与 rrf 的 top-3 重叠率 Jaccard。

## 实验 4：pool 消融

临时改 `pool=max(top_k*2,8)` 与 `top_k*8`，观察号码 query top-1 是否变化。

## 实验 5：单路对照

`mode=keyword` vs `mode=vector` 全量跑 `HYBRID_QUERIES`，填表。

---

## 报告模板

```markdown
# Fusion Lab
- query: 13900001111
- weighted top1:
- rrf top1:
- 结论:
```

---

## 常见实验坑

- 未 `set_retrieval_config` 后重建 `as_rag_service`  
- 忘记 `store.save()` 导致 API 与本地不一致  
- 用绝对分数比较两路 — 应看排名或 norm 后分数
"""


def _file24() -> str:
    return f"""# Phase 3 第七日总结（Day 31）

## 本周进度

| Day | 主题 | 版本 |
|-----|------|------|
| 25 | 知识库 MVP | 0.25.x |
| 26 | 多格式 | 0.26.x |
| 27 | 分块调参 | 0.27.x |
| 28 | rebuild | 0.28.x |
| 29 | Chroma | 0.29.x |
| 30 | 增量索引 | 0.30.x |
| **31** | **混合检索** | **{VER}** |

## Day 31 交付物

- HybridRetriever + RetrievalConfig  
- retrieval-config API  
- 17 tests  
- 30 篇课件  

## 核心能力

**读取侧**质量：精确 + 语义双路融合，可热配。

## 与 Phase 3 目标对齐

知识库从「能存」→「能快更」→「能答准」。Day 32 rerank 将进一步提升 top-k 精度。

## 学员自评 Rubric

| 等级 | 标准 |
|------|------|
| A | 能调 fusion + 写融合单测 |
| B | 能跑 demo 解释三模式 |
| C | 能复述 RRF 公式 |
| D | 仅会 pytest -q |

## 下周预告

Day 32：Cross-encoder rerank — 在 hybrid 召回后再用交叉编码器对 top-20 精排。

---

## Phase3 能力雷达（Day31 更新）

| 能力 | 等级 |
|------|------|
| 入库 | ★★★★★ |
| 增量 | ★★★★★ |
| 召回 | ★★★★☆ |
| 精排 | ★★☆☆☆（Day32） |
| 生成 | ★★★☆☆ |

---

## 团队复盘问题清单

1. 默认权重是否应地区化？  
2. 是否暴露 fusion 给运营 UI？  
3. 精确 query 集谁维护？  

---

## 第七日金句墙

- 「两条腿走路」——陈默  
- 「RRF 不吵架」——周航  
- 「号码是 keyword 的主场」——林晓  

---

## 提交给项目经理的一页纸

{REQ} 已交付：HybridRetriever、配置 API、17 测试、课件 30 篇。风险：权重需持续评估；缓解：RRF 备选。下一步：Day32 rerank。
"""


def _file25() -> str:
    return f"""# hybrid_api 脚本精读

## hybrid_api_demo.py 全文

{fenced("python", HYBRID_API_DEMO)}

---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| L13–L17 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| L21–L22 | 导入 TestClient 与 app 工厂 |
| L26 | `bootstrap_from_sample_docs` 保证可检索语料 |
| L27 | `set_knowledge_store` 测试注入单例 |
| L30–L31 | GET 默认 hybrid 配置 |
| L33–L37 | PUT 切 `fusion=rrf` — **API 核心演示** |
| L39–L40 | status 对账 retrieval_config |
| L42–L43 | chat 端到端 |
| L44 | health version `{VER}` |

---

## hybrid_demo.py 全文

{fenced("python", HYBRID_DEMO)}

`_top_source` 每次改 mode 后 `as_rag_service()` — 注意性能；教学可接受。

---

## constants.py

```python
HYBRID_QUERIES = (
    {{"query": "年化收益率可达", "expect_any": ("8%", "年化")}},
    {{"query": "13900001111", "expect_any": ("13900001111", "联系")}},
    {{"query": "投资有风险", "expect_any": ("风险", "谨慎")}},
)
```

三条覆盖语义 / 精确 / 合规关键词。

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day31/hybrid_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day31/hybrid_api_demo.py
pytest tests/day31/test_hybrid_api.py -v
```
"""


def _file26() -> str:
    return f"""# Day 31 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.hybrid_retriever; print('ok')"
pytest tests/day31/ --collect-only -q
```

**通过标准**：collect ≥17 tests，无 ImportError。

---

## Lab 1：读默认配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_retrieval_config().to_dict())
"
```

**通过标准**：`mode=hybrid`，`fusion` 为 weighted 或文档默认值。

---

## Lab 2：hybrid_demo 三模式（25 min）

```bash
python3 src/day31/hybrid_demo.py | tee /tmp/day31_demo.txt
```

**通过标准**：输出含三条 Q；每条有 vector/keyword/hybrid 三列；末尾 `✅`。

---

## Lab 3：切换 RRF（20 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, MODE_HYBRID
s = KnowledgeStore.bootstrap_from_sample_docs()
s.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=FUSION_RRF))
h = s.as_rag_service().index.retriever
print(h.search('投资有风险吗', top_k=3)[0].score)
"
```

**通过标准**：无异常；返回 1–3 条结果。

---

## Lab 4：weighted vs RRF 对比表（35 min）——必做

对 `HYBRID_QUERIES` 每条记录两种 fusion 的 top-1 `chunk_id` 是否相同。

**通过标准**：表格 ≥3 行；至少 1 条 query 两 fusion 不同或能解释为何相同。

---

## Lab 5：API demo（20 min）

```bash
python3 src/day31/hybrid_api_demo.py
```

**通过标准**：PUT 200；chat 200；打印 version 0.31.0。

---

## Lab 6：单测精读（25 min）

```bash
pytest tests/day31/test_hybrid_retriever.py::test_exact_phone_keyword_favors_hybrid -v
pytest tests/day31/test_hybrid_retriever.py::test_rrf_merge_helper -v
```

**通过标准**：2 passed；能口述测试意图。

---

## Lab 7：全量回归 + chat（20 min）

```bash
pytest tests/day31/ -q
curl -s -X POST http://127.0.0.1:8000/api/chat -H 'Content-Type: application/json' \\
  -d '{{"message":"最低起购金额？"}}' | jq '.reply | length'
```

（若无服务，用 `test_chat_with_hybrid_retrieval` 代替。）

**通过标准**：17 passed；chat reply 非空。

---

## 提交

`lab/day31-<姓名>.md` 含 Lab 4 表格 + Lab 7 截图。

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
| hybrid 与 vector 相同 | 增大 pool 或调权重 |
| PUT 422 | 检查 JSON mode 拼写 |
| 17 tests 失败 | 查 PYTHONPATH |

---

## 附录 A：Lab 4 表格模板

| query | weighted top1 | rrf top1 | 相同? |
|-------|---------------|----------|-------|
| 年化收益率可达 | | | |
| 13900001111 | | | |
| 投资有风险 | | | |

---

## 附录 B：curl retrieval-config 完整

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/retrieval-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"mode":"hybrid","fusion":"weighted","keyword_weight":0.35,"vector_weight":0.65,"rrf_k":60}}'
```

---

## 附录 C：17 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1 | test_retrieval_config_validate | retriever |
| 2 | test_hybrid_mode_vector_only | retriever |
| 3 | test_hybrid_mode_keyword_only | retriever |
| 4 | test_hybrid_weighted_merge | retriever |
| 5 | test_hybrid_rrf_merge | retriever |
| 6 | test_exact_phone_keyword_favors_hybrid | retriever |
| 7 | test_knowledge_store_persists_retrieval_config | retriever |
| 8 | test_status_includes_retrieval_config | retriever |
| 9 | test_rrf_merge_helper | retriever |
| 10 | test_weighted_merge_helper | retriever |
| 11 | test_health_version | api |
| 12 | test_get_retrieval_config_default_hybrid | api |
| 13 | test_put_retrieval_config_rrf | api |
| 14 | test_status_includes_retrieval_config | api |
| 15 | test_invalid_retrieval_mode_422 | api |
| 16 | test_chat_with_hybrid_retrieval | api |
| 17 | test_switch_to_keyword_mode | api |

---

## 附录 D：教师演示脚本（可复制）

```python
from rag.knowledge_store import KnowledgeStore
from rag.retrieval_config import RetrievalConfig, FUSION_RRF, FUSION_WEIGHTED, MODE_HYBRID

store = KnowledgeStore.bootstrap_from_sample_docs()
q = "13900001111"
for fusion in (FUSION_WEIGHTED, FUSION_RRF):
    store.set_retrieval_config(RetrievalConfig(mode=MODE_HYBRID, fusion=fusion))
    h = store.as_rag_service().index.retriever
    t = h.search(q, top_k=1)[0]
    print(fusion, t.chunk.source, t.score)
```

---

## 附录 E：Windows 注意

PowerShell 下 curl 别名可能是 Invoke-WebRequest；用 `curl.exe` 或 Python requests。

---

## 附录 F：与 Day30 Lab 差异

| 项 | Day30 | Day31 |
|----|-------|-------|
| 核心实验 | vocab 扩张 reset | fusion 对比 |
| 关键 API | upload | retrieval-config |
| 必读源码 | _incremental_index | hybrid_retriever |

---

## 附录 G：预期 Lab 7 输出

```
17 passed in 2.5s
```

---

## 附录 H：讲师时间盒

| Lab | 分钟 |
|-----|------|
| 0–1 | 25 |
| 2–3 | 45 |
| 4 | 35 |
| 5–7 | 65 |
"""


def _file27() -> str:
    return f"""# Day 32 预习：Rerank（交叉编码器重排）

**预告**：混合检索解决「召回」；rerank 解决「排准」— 对 hybrid 的 top-20 用 Cross-encoder 逐对打分重排。

陈默：「双路融合后，前 20 里仍可能有噪声 chunk。Day 32 用更贵的模型只看 query-chunk 对，把最相关的顶到第 1。」

## 预习问

1. 为何 rerank 不宜对全库运行，只对 top-N？  
2. Cross-encoder 与 bi-encoder（Day29 向量）差异？  

## Day32 路线图（预期）

| 模块 | 说明 |
|------|------|
| reranker.py | cross-encoder 或 mock 打分 |
| retrieval pipeline | hybrid → top-20 → rerank → top-3 |
| latency 预算 | rerank 增加 P95 但换 hit@1 |

## 与 Day31 关系

```
hybrid 召回 (宽) → rerank 精排 (尖) → LLM context
```

## 预习阅读

浏览 `rag/retriever.py` 的 `RetrievalResult` 结构，思考 rerank 如何原地替换 `score` 字段。

## 一句话

Day31 让正确答案**进候选**；Day32 让正确答案**排第一**。
"""


if __name__ == "__main__":
    write_course(31, build(), min_chars=110_000)
