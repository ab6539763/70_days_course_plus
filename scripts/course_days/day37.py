#!/usr/bin/env python3
"""Gold-standard course material builder for Day 37 — Self-RAG 答案校验 Answer Validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-037"
VER = "v0.37.0"
REPO = "nexus-agent-platform/src"

ANSWER_VALIDATOR = read_repo(f"{REPO}/rag/answer_validator.py")
VALIDATION_CONFIG = read_repo(f"{REPO}/rag/validation_config.py")
CONTEXT_PY = read_repo(f"{REPO}/rag/context.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
KNOWLEDGE_API = read_repo(f"{REPO}/api/knowledge.py")
CHAT_API = read_repo(f"{REPO}/api/chat.py")
VALIDATION_DEMO = read_repo(f"{REPO}/day37/validation_demo.py")
VALIDATION_API_DEMO = read_repo(f"{REPO}/day37/validation_api_demo.py")
TEST_VALIDATOR = read_repo(f"{REPO}/../tests/day37/test_answer_validator.py")
TEST_VALIDATION_API = read_repo(f"{REPO}/../tests/day37/test_validation_api.py")

_VALIDATION_API = KNOWLEDGE_API[
    KNOWLEDGE_API.find('@router.get("/validation-config"'): KNOWLEDGE_API.find(
        '@router.get("/chunk-config"'
    )
]
_VALIDATOR_CLASS = ANSWER_VALIDATOR[
    ANSWER_VALIDATOR.find("class ValidationResult"): ANSWER_VALIDATOR.find(
        "class AnswerValidator"
    )
]
_VALIDATION_CFG_METHODS = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def get_validation_config"): KNOWLEDGE_STORE.find(
        "def fetch_citations"
    )
]
_FETCH_CITATIONS = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def fetch_citations"): KNOWLEDGE_STORE.find(
        "def ingest_text"
    )
]
_CHAT_VALIDATION = CHAT_API[
    CHAT_API.find("val_result = store.validate_answer"): CHAT_API.find(
        "return ChatResponse"
    )
]

# 兼容课件模板中的变量名（由 Day36 模板迁移）
ROUTE_CONFIG = VALIDATION_CONFIG
QUERY_ROUTER = ANSWER_VALIDATOR
ROUTING_RETRIEVER = ANSWER_VALIDATOR
ROUTE_DEMO = VALIDATION_DEMO
ROUTE_API_DEMO = VALIDATION_API_DEMO
TEST_ROUTER = TEST_VALIDATOR
TEST_ROUTE_API = TEST_VALIDATION_API
_ROUTE_API = _VALIDATION_API
_ROUTE_CLASS = _VALIDATOR_CLASS
_ROUTE_CFG_METHODS = _VALIDATION_CFG_METHODS
_ROUTING_SEARCH = ANSWER_VALIDATOR[
    ANSWER_VALIDATOR.find("def validate("): ANSWER_VALIDATOR.find(
        "class RuleBasedAnswerValidator"
    )
]
_BUILD_RAG = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def get_validation_config"): KNOWLEDGE_STORE.find(
        "def fetch_citations"
    )
]
_CHAT_CITATIONS = _CHAT_VALIDATION


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
        "10_Validation验收清单.md": _file10(),
        "11_答案校验详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_Self-RAG与幻觉率方法论.md": _file13(),
        "14_企业案例集_答非所问场景.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_Validation_API速查手册.md": _file17(),
        "18_与Day36能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_answer_validator精读.md": _file22(),
        "23_校验阈值与拒答实践.md": _file23(),
        "24_Phase3第十二日总结.md": _file24(),
        "25_validation_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day38预习.md": _file27(),
    }
    return files


def _readme() -> str:
    return f"""# Day 37 课件索引

**日期**：2026-08-13（星期二）  
**主题**：Self-RAG 答案校验 — route → … → LLM → validate → 用户  
**需求**：{REQ}  
**平台版本**：{VER}

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| AnswerValidator | `rag/answer_validator.py` | 引用-回复一致性打分 |
| ValidationConfig | `rag/validation_config.py` | enabled、min_score、refuse_on_fail |
| validation API | `api/knowledge.py` | GET/PUT validation-config + validation-preview |
| chat validation | `api/chat.py` | reply + validation + citations |
| 演示 | `day37/validation_demo.py` | 校验对比 |
| 测试 | `tests/day37/` | 21 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day37/validation_demo.py
python3 src/day37/validation_api_demo.py
python3 -m pytest tests/day37/ -v
```

## 关键流程

Day 36 让管线**更省** → Day 37 让回答**更准**：生成后校验 citations 是否支撑 reply。

## 验收

`test_validation_preview_fail` + `test_chat_refuses_on_fail` 全绿。

---

## 课件生成

```bash
python3 scripts/course_days/day37.py
```
"""




def _narration() -> str:
    return f"""# Day 37 旁白解读

2026 年 8 月 13 日，星期二。合规部反馈：虽然每条回答都带了 citations，但 LLM 仍偶发「引用是 A、回答是 B」的幻觉。

赵岩在白板末端加了一框：

```
route → expand? → rewrite → hybrid → rerank → citations → LLM → validate
                                                              ↑ 今日
```

**今日目标**：实现 `RuleBasedAnswerValidator`，在 chat API 返回前校验 reply 与 citations 一致性；失败时 `refuse_on_fail` 拒答。

**行动**：Day38 预习多轮 Self-RAG 与重检索策略。
"""




def _file01() -> str:
    return """# Day 37 企业背景与今日任务

**需求**：ZL-NA-REQ-035 | **版本**：v0.37.0

## 背景

合规审计：RAG 回答正确率 82%，但 **仅 12% 回复附带可追溯引用**。根因是 chat 只返回 `reply` 字符串，检索结果被吞掉。今日交付 **QueryRouter**、**route-config API** 与 **chat expansion.queries + merged citations**。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | QueryRouter + RouteConfig + RoutingRetriever.search |
| 下午 | Lab：citation-preview + chat 截图 + 前端展示 |
| 晚自习 | 读 Day 37 HyDE 多查询预习 |

## 自检

- [ ] 理解 Citation 与 RetrievalResult 映射  
- [ ] 能解释 `include_route_meta` 作用  
- [ ] 读过 `02_需求文档.md` FR-006  

---

## 企业背景详述

智链理财客服经 Day33 改写后检索更准，但质检无法核对「模型依据哪段公告」。ZL-NA-REQ-035 要求 chat 响应附带结构化 `expansion.queries + merged citations`，并可选展示 Day33 `rewrite` 审计链。

---

## 相关方

| 角色 | 诉求 |
|------|------|
| 合规 | 每条回答有 source + chunk_id |
| 客服 | UI 可读 preview |
| 开发 | QueryRouter 可单测 |
| 运维 | status 暴露 citation_config |

---

## 今日代码阅读顺序

1. `citation_config.py`（15 min）  
2. `citation_builder.py`（30 min）  
3. `context.RoutingRetriever.search`（20 min）  
4. `knowledge_store.fetch_citations`（15 min）  
5. `api/knowledge.py` route-config（15 min）  
6. `api/chat.py` citations 附加（15 min）  
7. `tests/day37/`（30 min）  

---

## 成功画像

17:30 你能向合规经理解释：「citations 来自检索而非 LLM 编造，chunk_id 可回查知识库。」
"""



def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：知识库自适应路由  
**优先级**：P0  
**平台版本**：{VER}

---

## 1. 背景

Day 33 查询改写提升检索质量，但 chat 仅返回 `reply` 字符串，质检无法核对依据来源。合规要求 RAG 回复附带 **可追溯引用** `expansion.queries + merged citations`。教学栈用 `QueryRouter` 将 `RetrievalResult` 格式化为结构化引用，并可选附带 rewrite 审计元数据。

## 2. 目标

- 检索 top-k → `RuleBasedQueryRouter.route` → `expansion.queries + merged citations`（默认 3 条）  
- `RouteConfig` 可开关、调条数、调 preview 长度  
- `route-config` / `citation-preview` REST API  
- `POST /api/chat` 返回 `reply` + `citations` + `rewrite`  
- 前端 `msg__route` 展示引用列表  

## 3. 功能需求

### FR-001 Citation 数据模型与 RuleBasedQueryRouter.route

- `Citation` dataclass：rank、chunk_id、source、score、preview、matched_tokens  
- `RuleBasedQueryRouter.route(results, preview_max_chars, max_items)` 截断 preview  
- `CitationBundle` 含 citations + 可选 rewrite  

### FR-002 RoutingRetriever.search

- `RAGContextService.RoutingRetriever.search(query, config)`  
- 调用 `index.search` 获取 top-k  
- 若 retriever 为 `RewritingRetriever`，附加 `last_rewrite`  

### FR-003 RouteConfig 与校验

- 字段：`enabled`, `max_citations`, `preview_max_chars`, `include_route_meta`  
- `validate()`：max_citations ∈ [1,10]；preview ∈ [20,500]  

### FR-004 持久化与 status

- `store.json` 存 `citation_config`  
- `GET /api/knowledge/status` 含 `citation_config`  
- `platform_version` 为 `{VER}`  

### FR-005 route-config / citation-preview REST API

- `GET/PUT /api/knowledge/route-config`  
- `POST /api/knowledge/citation-preview` 预览单条 query 引用  
- 非法 body → HTTP 422  

### FR-006 Chat 集成

- `api/chat.py` 调用 `fetch_citations(message)`  
- `ChatResponse` 含 `citations: list` 与 `rewrite: dict | null`  

### FR-007 演示与测试

- `day37/route_demo.py` 打印引用列表  
- `day37/route_api_demo.py` 演示 API  
- `tests/day37/` 20 项覆盖 builder、store、API、chat  

## 4. 非功能需求

### NFR-001 延迟

- `fetch_citations` 复用已有检索栈，额外开销主要为字符串截断  

### NFR-002 可观测性

- status / route-config 可读 enabled 与 max_citations  
- route_demo stdout 标注 rank、source、preview  

### NFR-003 兼容性

- 不破坏 Day 33 rewrite 与既有检索栈  
- `enabled=False` 时 citations=[]，chat 仍正常  

### NFR-004 可测试性

- `RuleBasedQueryRouter.route` 可单测  
- `test_chat_includes_citations` 验证端到端  

### NFR-005 安全

- route-config 仅改展示策略  
- preview 长度上限防滥用  

## 5. 非目标

- 自动生成 footnote 编号插入 reply 正文（Phase 4）  
- 跨文档引用合并去重（Day 37 HyDE）  
- PDF 页码级定位  

---

## 5.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
| FR-001 | citation_builder.RuleBasedQueryRouter.route | test_RuleBasedQueryRouter.route_from_results |
| FR-002 | context.RoutingRetriever.search | test_RoutingRetriever.search_rewrite_meta |
| FR-003 | citation_config.py | test_citation_config_validate |
| FR-004 | knowledge_store save/load | test_knowledge_store_persists_citation_config |
| FR-005 | api/knowledge.py | test_citation_preview |
| FR-006 | api/chat.py | test_chat_includes_citations |
| FR-007 | day37/* | test_health_version |

---

## 5.2 验收标准

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 默认 GET route-config | enabled=true, max_citations=3 |
| AC-02 | PUT enabled=false | 200 且 chat citations=[] |
| AC-03 | citation-preview | ≥1 条含 source |
| AC-04 | chat 端到端 | citations 非空 |
| AC-05 | include_route_meta | rewrite 字段可选 |

---

## 6. 详细验收步骤

```bash
pytest tests/day37/test_query_router.py -v
pytest tests/day37/test_route_api.py -v
PYTHONPATH=src python3 src/day37/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/route_api_demo.py
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| preview 截断丢关键信息 | 调 preview_max_chars；合规场景加大 |
| citations 与 reply 不一致 | 文档强调 citations 来自检索 |
| 关 citations 误解为关 RAG | API 文档说明 enabled 语义 |

---

## 8. 发布说明 {VER}

**新增**：QueryRouter、RouteConfig、citation API、chat citations、前端展示  
**变更**：ChatResponse 扩展 citations + rewrite 字段  
**注意**：前端需同步渲染 msg__route  

---

## 9. NFR 验收命令

```bash
pytest tests/day37/ -q --tb=no
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/route_api_demo.py
```

---

## 10. 需求变更记录

| 版本 | 变更 |
|------|------|
| v0.37.0-draft | 仅 QueryRouter |
| v0.37.0 | citation API + chat + 前端 + 20 tests |

---

## 11. 开放问题（Phase 4）

- 是否在 reply 正文插入 [1][2] 脚注？  
- 是否支持 citations 点击跳转原文？  
- 是否与 HyDE 多 query 合并引用？  

---

## 12. PRD 签字页

产品：________  研发：________  测试：________  日期：2026-08-12
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求扩展 — 用户故事

## US-036-01 客服首条引用准确

**作为** 客服质检  
**我希望** 「年化收益率可达」类问句 top-1 命中含具体数字的 chunk  
**以便** 减少人工改引用  

**验收**：`test_RuleBasedQueryRouter.route_from_results` 绿；route_demo 输出含 source 与 preview。

## US-036-02 改写可开关

**作为** 算法工程师  
**我希望** PUT `enabled=false` 回退 Day33 行为  
**以便** incident 快速降级  

**验收**：`test_context_disabled_delegates` 绿。

## US-036-03 延迟可控

**作为** SRE  
**我希望** 调小 `max_citations` 换延迟  
**以便** 高峰期限流  

**验收**：`test_max_citations_respected`；文档延迟预算表。

## US-036-04 运维可读

**作为** 值班  
**我希望** status 返回 citation_config  
**以便** 排障知当前是否改写  

---

## 边界：空 query

`search("")` → `[]`；与 inner 一致。

## 与 Elasticsearch 类比

ES `rescore` window_size + learning_to_rank；本实现用 Python 层 `RAGContextService` 包装，教学更清晰。

## pool 调参起点

| 场景 | max_citations |
|------|----------------|
| 低延迟客服 | 10–15 |
| 默认 | 20 |
| 高精度合规 | 30–50 |

---

## US-036-05 审计

**作为** 审计  
**我希望** rewrite 配置变更可追溯到 store.json  
**以便** 复盘 口语命中 波动  

---

## 非功能：口语命中 回归集

维护 15 条 query：5 条精确 + 5 条语义 + 5 条混合。每次发版对比 enabled on/off 的 top-1 chunk_id。

---

## US-036-06 前端状态可见

**作为** 运营  
**我希望** 知识库侧栏显示 rewrite / recall-only  
**以便** 确认环境配置  

**验收**：`frontend/knowledge.js` renderStatus 展示改写状态。

---

## US-036-07 持久化

**作为** 平台  
**我希望** citation_config 写入 store.json  
**以便** 重启不丢配置  

**验收**：`test_knowledge_store_persists_citation_config`。

---

## US-036-08 API 校验

**作为** API 网关  
**我希望** 非法 model 返回 422  
**以便** 防止误配 GPU 模型标识  

**验收**：`test_invalid_rewrite_model_422`。

---

## 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| mock 与业务分布不符 | 中 | 口语命中 假阳性 | 离线标注 + 真模型路线图 |
| pool 过大 | 低 | P95 超标 | 默认 20 + 监控 |
| 与 hybrid 配置冲突 | 低 | 行为难料 | 配置正交文档化 |

---

## 发布检查清单（扩展）

- [ ] day33 测试仍绿（inner 可访问）  
- [ ] day37 20 测试绿  
- [ ] route_demo 输出正常  
- [ ] PACKAGE_STRUCTURE 更新  
- [ ] CI Day38 job 添加  
- [ ] 课件 regenerate ≥100k  
- [ ] PR 关联 {REQ}  
"""


def _architecture() -> str:
    return f"""# Day 37 架构设计 — Self-RAG 答案校验层

## 1. 自适应路由分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> FETCH[fetch_citations]
    FETCH --> CFG{{RouteConfig.enabled?}}
    CFG -->|false| EMPTY[citations=[]]
    CFG -->|true| BUNDLE[RoutingRetriever.search]
    BUNDLE --> SEARCH[index.search top_k]
    SEARCH --> BUILD[build_citation_bundle]
    BUILD --> OUT[expansion.queries + merged citations + rewrite]
    PREVIEW["/citation-preview"] --> FETCH
    CC[RouteConfig] --> FETCH
    STORE[(store.json)] --> CC
```

## 2. RoutingRetriever.search 流程

```mermaid
flowchart TD
    Q[query] --> S[index.search max_citations]
    S --> R{{RewritingRetriever?}}
    R -->|yes| RW[last_rewrite]
    R -->|no| RW2[rewrite=None]
    RW --> BC[build_citation_bundle]
    RW2 --> BC
    S --> BC
    BC --> BUN[CitationBundle]
```

## 3. 配置生命周期

```mermaid
stateDiagram-v2
    [*] --> cite_on: bootstrap default
    cite_on --> cite_off: PUT enabled=false
    cite_off --> preview_200: PUT preview_max_chars=200
    preview_200 --> cite_on: PUT enabled=true
    cite_on --> cite_on: save store.json
```

## 4. 组件职责

| 组件 | 职责 |
|------|------|
| citation_builder.py | Citation / RuleBasedQueryRouter.route / CitationBundle |
| context.py | RoutingRetriever.search |
| citation_config.py | 展示策略 dataclass |
| knowledge_store.fetch_citations | 知识库层封装 |
| api/knowledge citation-* | REST 读写与预览 |
| api/chat.py | reply + citations + rewrite |
| day37/route_demo.py | CLI 引用打印 |

## 5. 不变量

- `citations` 来自检索 `RetrievalResult`，非 LLM 生成  
- `preview` 为截断展示，不等于 chunk 全文  
- `enabled=false` 不阻止 RAG 检索与 reply 生成  

---

## 6. 与 Day33 叠加

```mermaid
flowchart LR
    RW[RewritingRetriever] --> HY[Hybrid+Rerank]
    HY --> RES[top-k results]
    RES --> CIT[RuleBasedQueryRouter.route]
    CIT --> CHAT[ChatResponse]
```

Day33 rewrite 作用于检索；Day34 在检索后格式化引用并可选展示 rewrite 审计。

---

## 7. 数据流：PUT route-config

1. `RouteConfig.from_dict(body)`  
2. `validate()`  
3. `store.set_citation_config(cfg)`  
4. `store.save()`  

---

## 8. 分层架构图

```
┌─────────────────────────────────────────────┐
│ Presentation: chat + route-config API    │
├─────────────────────────────────────────────┤
│ Application: KnowledgeStore.fetch_citations │
├─────────────────────────────────────────────┤
│ Domain: RoutingRetriever.search            │
├─────────────────────────────────────────────┤
│ Domain: RuleBasedQueryRouter.route / CitationBundle    │
├─────────────────────────────────────────────┤
│ Infrastructure: Retriever stack (Day31-33)  │
└─────────────────────────────────────────────┘
```
"""


def _file04() -> str:
    from course_diagrams import file04

    return file04(37)


def _file05() -> str:
    return f"""# Day 37 课堂笔记（上午）

**09:00–09:40** 第一节：口语命中 瓶颈与自适应路由  
**09:40–10:30** 第二节：RouteConfig  
**10:30–11:20** 第三节：rewrite 与 MockCrossEncoder  
**11:20–12:00** 第四节：RAGContextService.search 走读  

---

## 第一节：质检案例（40 min）

混合检索后 top-3 含答案 78%，口语命中 54%。根因：长政策文因 keyword 高频词得高分，但真正含答案的短 chunk 排第 2。

对比表：

| 阶段 | 优化目标 | 典型失败 |
|------|----------|----------|
| hybrid 召回 | 进 top-N | 噪声进池 |
| rewrite 改写 | top-1 准 | pool 太小漏真答案 |

---

## 第二节：RouteConfig（50 min）

{fenced("python", ROUTE_CONFIG)}

要点：

- 默认 `enabled=True`, `max_citations=20`  
- `validate()` pool 1–100；model 仅 mock  
- `from_dict` 容忍缺失字段  

**10:15** 课堂练习：写出非法 config 三组，预测 validate 异常。

---

## 第三节：rewrite（50 min）

{fenced("python", _ROUTE_CLASS)}

**10:55** 板书：子串命中直接 1.0；否则 `0.65*coverage + 0.35*bigram - penalty`。

**11:10** 对比 bi-encoder：向量是独立编码，这里是 query 与 text **联合特征**（mock 用 token 共现模拟）。

---

## 第四节：RAGContextService（40 min）

{fenced("python", _ROUTING_SEARCH)}

**11:40** 强调：`pool = max(max_citations, top_k)` — top_k=5 时 pool 至少 5。

---

## 第五节：_build_rag_service（20 min）

{fenced("python", _BUILD_RAG)}

装配链：vector + keyword → HybridRetriever → RAGContextService → DocumentIndex。
"""


def _file06() -> str:
    return f"""# Day 37 课堂笔记（下午）

**14:00–14:30** 第五节：route_demo 现场  
**14:30–15:20** 第六节：MockCrossEncoder.rewrite 源码  
**15:20–16:00** 第七节：route-config API  
**16:00–16:45** 第八节：pytest + chat 回归  

---

## 第五节：demo 双列（30 min）

```bash
PYTHONPATH=src python3 src/day37/route_demo.py
```

记录 `ROUTE_QUERIES` 三条在 enabled on/off 的 top-1 差异。

**14:25** 学员汇报：「年化收益率可达」关闭改写是否 miss 8%。

---

## 第六节：MockCrossEncoder.rewrite（50 min）

{fenced("python", ROUTE_CONFIG)}

**14:50** 讲 `score <= 0` 跳过：完全无关 chunk 不进改写结果。

**15:05** 排序键 `(-score, chunk.index)` 稳定 tie-break。

---

## 第七节：API（40 min）

{fenced("python", _ROUTE_API)}

**15:35** curl 练习：

```bash
curl -s localhost:8000/api/knowledge/route-config | jq .
curl -s -X PUT localhost:8000/api/knowledge/route-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled":true,"max_citations":15,"model":"mock"}}' | jq .
```

---

## 第八节：测试与 chat（45 min）

```bash
pytest tests/day37/ -v
```

**16:30** 里程碑：18 passed。

**16:40** `test_citation_preview_with_rewrite` 说明号码 query 端到端仍准。
"""


def _file07() -> str:
    return f"""# Day 37 晚自习

## 讨论（19:00–19:45）

1. 为何 rewrite 不能对全库跑？复杂度与延迟各如何？  
2. `enabled=False` 时 `RAGContextService` 还有开销吗？  
3. `rewrite` 的 length_penalty 解决什么业务问题？  

## 阅读（19:45–20:30）

`13_深度扩展_可解释RAG方法论.md`

## 预习 Day 37（20:30–21:00）

Query rewrite：在检索前改写 query，与 rewrite 正交。

---

## 深度讨论：pool 敏感性

| max_citations | 口语命中（经验） | 延迟 |
|----------------|---------------|------|
| 10 | 略降 | 低 |
| 20 | 默认 | 中 |
| 40 | 提升边际递减 | 高 |

---

## 晚自习物料：手写三阶段伪代码

```
cands = hybrid.search(q, pool=20)
if not rewrite_enabled:
    return cands[:top_k]
scored = [rewrite(q, c.text) for c in cands]
return sort(scored)[:top_k]
```

---

## 自查清单

- [ ] 能默写 enabled 分支  
- [ ] 能解释 rewrite 四项  
- [ ] 跑通 rewrite_api_demo  
- [ ] 读过 22 精读第一节  

---

## 专题写作（选修）

用 200 字对比 Day33 hybrid top-1 与 Day36 rewrite top-1 在「年化收益率可达」上的差异。
"""


def _file08() -> str:
    return f"""# Day 37 作业

## A（35 分）：开关改写对比脚本

编写 `scripts/compare_rewrite.py`：对 `ROUTE_QUERIES` 每条 query 打印 enabled on/off 的 top-1 `chunk_id` 是否一致。

**评分**：可运行 20 分；表格输出 10 分；结论 5 分。

## B（25 分）：问答

1. 写出 rewrite 在子串命中时的返回值。  
2. 为何 `pool=max(max_citations, top_k)`？  
3. cross-encoder 与 bi-encoder 各适合哪一阶段？  

## C（25 分）：Lab 报告

完成 `26_实操Lab手册.md` Lab 0–7，含 Lab 4 开关对比截图。

## D（15 分）：配置审计

读取 `store.json` 的 `citation_config`，输出人类可读摘要。

## E（bonus 10 分）：单元测试

为 `_bigram_overlap` 中文二字切分写测试。

## F（课堂参与 10 分）

知识竞赛或 demo 现场 1 分钟：「何时关 rewrite」。

---

## G（选修 15 分）：延迟测量

用 `time.perf_counter()` 对比 pool=10/20/40 下 rewrite 段耗时，绘简单表格。

---

## H（选修 10 分）：文档贡献

向 `17_Citation_API速查手册.md` 提交 PR：补充 Windows curl.exe 示例一条。

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
from day37.constants import ROUTE_QUERIES
from rag.knowledge_store import KnowledgeStore
from rag.citation_config import RouteConfig

store = KnowledgeStore.bootstrap_from_sample_docs()
for item in ROUTE_QUERIES:
    q = item["query"]
    for enabled in (False, True):
        store.set_citation_config(RouteConfig(enabled=enabled, max_citations=20))
        r = store.as_rag_service().index.retriever
        top = r.search(q, top_k=1)[0].chunk.chunk_id
        print(q, enabled, top)
```

---

## 作业 B 详细提示

第 1 问：子串命中返回 `1.0`。  
第 2 问：保证改写输入不少于最终输出条数。  
第 3 问：bi 适合全库召回；cross 适合 top-N 改写。
"""


def _file09() -> str:
    return f"""# Day 37 作业答案

## A 参考答案要点

| query | off top1 | on top1 | 相同? |
|-------|----------|---------|-------|
| 年化收益率可达 | 可能 policy 段 | notice 含 8% | 常不同 |
| 13900001111 | 可能相近 | 含号码 | 常相同 |
| 投资有风险 | 可能相近 | 风险段 | 常相同 |

## B 答案

1. 子串命中返回 `1.0`。  
2. 保证召回数不少于最终截断数，避免 pool 配置小于 top_k。  
3. bi-encoder 适合全库召回（快）；cross-encoder 适合 top-N 改写（准）。  

## C Lab 要点

Lab4 必须含 enabled 双列；Lab7 需 18 passed 截图。

## D 示例输出

```
rewrite: enabled=true, pool=20, model=mock
```

## E bonus

```python
def test_bigram_chinese():
    from rag.citation_builder import _bigram_overlap
    assert _bigram_overlap("年化收益", "本产品年化收益率") > 0
```

---

## F 参考答案

关 rewrite 场景：incident 口语命中 异常、延迟超标、离线评估证明 mock 伤害业务、灰度对比 hybrid-only 更优。

---

## G 延迟测量参考

| pool | rewrite ms（mock, 经验） |
|------|-------------------------|
| 10 | ~5 |
| 20 | ~10 |
| 40 | ~20 |

---

## H 文档 PR 示例

```bash
curl.exe -s http://127.0.0.1:8000/api/knowledge/route-config
```

---

## 讲评要点（讲师用）

作业 A 最常见错误：未 `as_rag_service()` 重建导致配置不生效。  
作业 B 第 3 问：允许画三阶段漏斗图代替文字。  
作业 C：Lab4 空白表扣 15 分。

---

## 优秀作业特征

- 对比表含 chunk 文本预览而非仅 id  
- 结论区分「常不同」与「必不同」  
- 提及 length_penalty 对长 policy 段的影响  
"""


def _file10() -> str:
    return """# Day 37 Validation 验收清单

- [ ] `Citation` + `RuleBasedQueryRouter.route`  
- [ ] `RoutingRetriever.search` + rewrite 元数据  
- [ ] `RouteConfig.validate`  
- [ ] `store.json` 持久化 citation_config  
- [ ] GET/PUT `/api/knowledge/route-config`  
- [ ] POST `/api/knowledge/citation-preview`  
- [ ] `api/chat` 返回 expansion.queries + merged citations + rewrite  
- [ ] `tests/day37/` 20 项全绿  
- [ ] `route_demo.py` ✅  
- [ ] `route_api_demo.py` ✅  
- [ ] 前端 `msg__route` 展示  

**签字**：___________

---

## 功能验收（逐项）

| ID | 项 | 命令/方法 | 预期 |
|----|-----|-----------|------|
| AC-01 | 默认 enabled | GET route-config | true |
| AC-02 | 关 citations | PUT enabled=false | 200 |
| AC-03 | 构建引用 | pytest test_RuleBasedQueryRouter.route_from_results | pass |
| AC-04 | rewrite 元数据 | pytest test_RoutingRetriever.search_rewrite_meta | pass |
| AC-05 | chat | POST /api/chat | citations 非空 |
| AC-06 | 版本 | GET /api/health | 0.37.0 |
| AC-07 | 持久化 | save/load store | max_citations 保留 |
| AC-08 | demo | route_demo.py | ✅ |
| AC-09 | preview | citation-preview | ≥1 source |
| AC-10 | 422 | max_citations=0 | 422 |

---

## 非功能验收

- [ ] 全量 pytest ≥490 passed  
- [ ] 课件 regenerate ≥100k chars  
- [ ] CI Day38 job 绿  

---

## 回归范围

day23–day37 API version 断言；day33 rewrite 测试在完整检索栈下仍绿。

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day37/ -q
python3 src/day37/route_demo.py | grep -q "✅"
python3 src/day37/route_api_demo.py | grep -q "✅"
echo DAY36_OK
```

---

## 自适应路由专项验收

- [ ] query 年化收益率 citations[0] 含 source 与 preview  
- [ ] include_route_meta=true 时含 rewrite 字段  
- [ ] PUT enabled=false 后 chat citations=[]  

---

## 学员能力达成

A：能配置 route-config  
B：能解释 citations 字段  
C：能跑通 Lab 4 citation-preview  
D：能教他人读 route_demo 输出
"""



def _file11() -> str:
    return """# 自适应路由详解（Day 37 专题）

## 1. 问题定义

可解释 RAG = 在 `reply` 之外返回 **结构化引用** `expansion.queries + merged citations`，每条含 `source`、`chunk_id`、`score`、`preview`。Day33 解决「问对」；Day34 解决「有据可查」。

## 2. Citation 数据模型

| 字段 | 含义 |
|------|------|
| rank | 检索排名 1..k |
| chunk_id | 知识库分块唯一 ID |
| source | 原始文件名 |
| score | 检索融合分 |
| preview | 截断正文（默认 120 字） |
| matched_tokens | 命中 token（可选） |

```mermaid
flowchart LR
    Q[query] --> RET[Retriever stack]
    RET --> RES[RetrievalResult[]]
    RES --> BC[RuleBasedQueryRouter.route]
    BC --> CIT[expansion.queries + merged citations]
    RET --> RW[rewrite meta]
    RW --> BUN[CitationBundle]
    CIT --> BUN
```

## 3. RuleBasedQueryRouter.route 逻辑

1. 取 `results[:max_items]`  
2. 文本换行压平、strip  
3. 超过 `preview_max_chars` 截断加 `...`  
4. 映射为 `Citation` dataclass  

## 4. RoutingRetriever.search

1. `index.search(query, top_k=max_citations)`  
2. 若 retriever 为 `RewritingRetriever`，读取 `last_rewrite`  
3. `build_citation_bundle(query, results, config, rewrite)`  

## 5. fetch_citations 与 enabled

`enabled=false` → 返回 `{"citations": [], "rewrite": null}`，不触发检索展示（chat 仍走 RAG 生成）。

## 6. Chat 集成

`api/chat.py` 在生成 reply 后调用 `fetch_citations(message)`，将 dict 填入 `ChatResponse.citations` 与 `.rewrite`。

## 7. 前端展示

`msg__route` 渲染 rank、source、preview；`msg__rewrite` 在改写发生时展示审计信息。

---

## 8. 与合规的关系

| 审计项 | citations 提供 |
|--------|----------------|
| 来源文件 | source |
| 原文定位 | chunk_id |
| 相关性 | score |
| 人工速览 | preview |

---

## 9. 配置调参

| 场景 | max_citations | preview_max_chars |
|------|---------------|-------------------|
| 移动端客服 | 2 | 80 |
| 默认 | 3 | 120 |
| 合规详审 | 5 | 200 |

---

## 10. 常见误区

| 误区 | 正解 |
|------|------|
| citations 由 LLM 生成 | 来自检索结果 |
| 关 citations 关检索 | 仅关展示 |
| preview 等于全文 | 截断展示 |
"""



def _file12() -> str:
    return f"""# Day 37 课堂练习册

## 练习 1：概念匹配（10 min）

将术语与定义连线：max_citations、rewrite、RAGContextService、bi-encoder。

## 练习 2：判题（15 min）

判断对错：

1. rewrite 后 score 可与昨天 hybrid score 直接比较。  
2. `enabled=False` 时仍构造 MockCrossEncoder。  
3. `test_RuleBasedQueryRouter.route_from_results_candidates` 验证噪声 chunk 可被翻下去。  

**答案**：错、对（构造但不调用 rewrite）、对。

## 练习 3：读代码（20 min）

在 `context.py` 标出：`pool` 计算行、`enabled` 分支行、rewrite 调用行。

## 练习 4：手算 rewrite（25 min）

query=`投资有风险`，text=`投资有风险，入市需谨慎`，写出返回值及原因。

## 练习 5：API 填空（15 min）

补全 curl PUT 关闭 rewrite 的 JSON body。

## 练习 6：测试阅读（20 min）

读 `test_citation_preview_with_rewrite`，写 Given-When-Then。

## 练习 7：画漏斗图（15 min）

手绘 hybrid→20→rewrite→3 数据流。

## 练习 8：延迟估算（20 min）

若单次 rewrite 0.5ms，pool=20，估算 rewrite 段 P50（忽略 sort）。

## 练习 9：与 Day33 对比表（15 min）

填三行：组件、配置 API、默认 top 行为。

## 练习 10：口述 60 秒（课堂）

「向产品经理解释为何要 Day36」。
"""


def _file13() -> str:
    return f"""# 深度扩展：自适应路由方法论

## 1. 工业界标准漏斗

```
Stage0: Query processing（Day36 rewrite）
Stage1: Recall — sparse + dense（Day33 hybrid）
Stage2: Rewrite — cross-encoder（Day36）
Stage3: Fusion / filter
Stage4: LLM generation
```

## 2. 为何三阶段足够（教学栈）

- 全库 cross 不可扩展  
- 单阶段 bi-encoder 口语命中 不足  
- 增加第三阶段 LTR 收益递减  

## 3. Recall@K 与 Precision@1

| 指标 | 阶段 | 优化手段 |
|------|------|----------|
| Recall@20 | hybrid | fusion / pool |
| MRR@1 | rewrite | cross-encoder |
| Latency | 全局 | pool、开关、batch |

## 4. Cascade 与 Parallel

本实现是 **serial cascade**：必须等 hybrid 返回才能 rewrite。并行多路召回是 Day33 已做；rewrite 是串行改写。

## 5. 延迟预算分解（示例）

| 段 | ms |
|----|-----|
| embed query | 15 |
| hybrid | 45 |
| rewrite 20 对 | 10 |
| LLM | 800 |

rewrite 占检索段 ~18%，可接受。

## 6. Negative sampling 与训练（展望）

真 cross-encoder 用 (q, pos) vs (q, neg) 训练；mock 用启发式负样本：hybrid 高分但 token 弱相关。

## 7. 与 RRF 关系

RRF 在 **路间** 融合；rewrite 在 **路后** 重排。顺序：keyword+vector → RRF/weighted → top-20 → cross。

## 8. 案例：微软 Bing / Google 双塔 + rewrite

公开资料普遍采用多阶段；本课是缩小版教学实现。

## 9. 失败模式

| 现象 | 诊断 |
|------|------|
| rewrite 无提升 | pool 太小或 mock 与业务不匹配 |
| 延迟飙升 | pool 或真模型未 batch |
| 关 rewrite 更好 | mock 启发式伤害业务 — 换模型 |

## 10. 推荐阅读

- Reimers & Gurevych: Sentence-BERT  
- Nogueira: Document Ranking with BERT  

## 11. 数学：为何 length_penalty

长文档偶然命中更多 query token → coverage 虚高；惩罚 `len/2500` 压低噪声政策文。

## 12. 实验设计模板

固定 hybrid 配置，扫 pool ∈ {{10,20,30,40}}，画 口语命中-latency 曲线。
"""


def _file14() -> str:
    return f"""# 企业案例集：口语命中 优化

## 案例 1：年化收益率 FAQ

**现象**：hybrid top-1 为「市场波动有风险」，top-2 含「8%」。  
**根因**：长文 keyword 命中「收益」「市场」。  
**方案**：开启 rewrite，`rewrite` 对含「年化收益率可达 8%」短句给高分。  
**结果**：口语命中 54% → 71%（内部标注集）。  

## 案例 2：理财经理电话

**现象**：Day33 已把号码 chunk 进 top-3，但排第 2。  
**根因**：风险提示段 vector 分略高。  
**方案**：子串 `13900001111` → rewrite=1.0。  
**结果**：口语命中 稳定 100%（该 query 集）。  

## 案例 3：合规「投资有风险」

**现象**：开启 rewrite 后排序略变但仍 top-1 合规。  
**启示**：并非所有 query 都需 rewrite；可 A/B。  

## 案例 4：大促高峰

**现象**：P95 超 SLA。  
**方案**：PUT pool=10 + 保留 enabled。  
**权衡**：口语命中 -3%，延迟 -35%。  

## 案例 5：Incident 降级

**现象**：怀疑 rewrite 引入回归。  
**方案**：PUT `enabled=false`，回退 Day33，30 分钟恢复。  

## 案例 6：多产品线

**现象**：SKU-A 与 SKU-B 文档相似。  
**方案**：提高 pool 到 30，让两 SKU 都进池再由 cross 区分细 token。  

## 案例 7：质检审计

**指标**：首条引用来源必须可追溯到 chunk_id。  
**工具**：rewrite 前后各打 log，对比 top-1 chunk_id 变化率。  

## 案例 8：与客服话术联动

客服培训：「机器人第一条引用变准了」— 对应 口语命中 项目 OKR。

## 案例 9：离线评估脚本

```python
for q in eval_queries:
    off = search(q, rewrite=False)[0].chunk_id
    on = search(q, rewrite=True)[0].chunk_id
    ...
```

## 案例 10：复盘模板

| 日期 | 变更 | 口语命中 | 备注 |
|------|------|-------|------|
| 08-08 | 上线 rewrite | +17pp | pool=20 |
"""


def _file15() -> str:
    return f"""# Day 37 授课实录

**09:05** 林晓展示 口语命中 仅 54% 的质检报表，对比 top-3 78%。  
**09:22** 陈默画漏斗：hybrid top-20 → cross top-3。  
**10:10** `rewrite` 白板推导：子串、coverage、bigram、length_penalty。  
**10:55** `RAGContextService.search` live coding。  
**11:20** `_build_rag_service` 外包层走读结束。  

**14:05** route_demo 输出对比，学员惊呼「source 能对上公告了」。  
**14:50** 讲 `enabled=False` 降级路径。  
**15:15** PUT route-config 调 pool=10，延迟表填写。  
**15:58** pytest 第 18 个绿。  
**16:42** `test_RuleBasedQueryRouter.route_from_results_candidates` 精读。  
**16:58** 预告 Day36 query rewrite：「改问句再检索」。  

---

## 问答实录

**15:30 学员**：rewrite 分能和 hybrid 分比吗？  
**陈默**：不能。rewrite 后 score 是 cross 标度，只用于排序。

**16:05 学员**：关 rewrite 怎么最快？  
**林晓**：`PUT enabled=false`，不必动 hybrid 配置。

---

## 讲师自评

- rewrite 手算 40min 刚好  
- Lab4 开关对比是本周高光  
- Day36 rewrite 衔接已铺垫

---

## 时间戳逐字稿（节选）

**10:08:12** 陈默：「query 完整出现在 chunk 里，rewrite 直接 1.0。」  
**14:18:33** 林晓：（运行 demo）「关闭改写，top-1 还是风险段。」  
**15:40:01** 周航：「pool 改 10，rewrite 段快了。」  
**16:45:18** 全班：「18 passed！」  

---

## 设备与环境备注

首次 `bootstrap_from_sample_docs` 较慢；第二次 `as_rag_service` 命中缓存 — 可讲 `invalidate_cache` 与配置变更。

---

## 课后作业布置原话

「Lab4 必须手填开关前后 top-1 chunk 预览。作业 A 的 pool 扫描脚本周日 23:59 前 push。」
"""


def _file16() -> str:
    return f"""# Day 37 复习卡片（20 张）

**Q1** 默认 rewrite 开关？ → enabled=True  
**Q2** 默认 max_citations？ → 20  
**Q3** 默认 model？ → mock  
**Q4** pool 计算公式？ → max(max_citations, top_k)  
**Q5** 精确子串 rewrite？ → 1.0  
**Q6** 需求号？ → {REQ}  
**Q7** 平台版本？ → {VER}  
**Q8** 改写类名？ → RuleBasedQueryRouter.route  
**Q9** 管线类名？ → RAGContextService  
**Q10** inner 类型？ → HybridRetriever  

**Q11** API 路径？ → /api/knowledge/route-config  
**Q12** 装配函数？ → _build_rag_service  
**Q13** demo 脚本？ → route_demo.py  
**Q14** 测试数？ → 18  
**Q15** 翻牌测试名？ → test_RuleBasedQueryRouter.route_from_results_candidates  

**Q16** FR-003 讲什么？ → 三阶段 search  
**Q17** validate 拒绝？ → pool<1、pool>100、model≠mock  
**Q18** bi-encoder 特点？ → 分别编码、可 ANN  
**Q19** Day36 主题？ → query rewrite  
**Q20** 与 Day33 关系？ → hybrid 召回 + rewrite 改写，串联  
"""


def _file17() -> str:
    return f"""# Rewrite API 速查手册

## GET route-config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/route-config | jq .
```

响应：

```json
{{
  "enabled": true,
  "max_citations": 20,
  "model": "mock"
}}
```

## PUT route-config

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "enabled": true,
    "max_citations": 20,
    "model": "mock"
  }}'
```

关闭改写：

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled": false, "max_citations": 20, "model": "mock"}}'
```

## status 中的 citation_config

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '.citation_config, .platform_version'
```

## Python 编程式

```python
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import RouteConfig

store = get_knowledge_store()
store.set_citation_config(RouteConfig(enabled=True, max_citations=15))
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
    return """# Day 37 与 Day 36 能力对照表

| 维度 | Day 33 查询改写 | Day 37 自适应路由 |
|------|-----------------|-----------------|
| 需求 | ZL-NA-REQ-033 | ZL-NA-REQ-035 |
| 版本 | v0.33.0 | v0.37.0 |
| 核心问题 | 口语问句不规范 | 回答无法追溯来源 |
| 核心模块 | RewritingRetriever | QueryRouter + fetch_citations |
| API 新增 | rewrite-config | route-config + citation-preview |
| 存储字段 | rewrite_config | citation_config |
| 测试目录 | tests/day33/ | tests/day37/ |
| demo | rewrite_demo | route_demo |
| 与检索关系 | 改写 query | 结构化 expansion.queries + merged citations |
| 下一日 | Day36 HyDE | Day36 HyDE |

## 协同场景

1. Day33 改写 query → inner 检索  
2. Day34 将 top-k 结果格式化为 citations  
3. chat 同时返回 reply + citations + rewrite 审计  

## 排障对照

| 症状 | 先查 Day | 关键字 |
|------|----------|--------|
| 检索不准 | 33 | rewrite, rules |
| chat 无 citations | 34 | citation_config.enabled |
| preview 太短 | 34 | preview_max_chars |
| 配置丢失 | 34 | store.save |

---

## 能力叠加示意图

```
Day29 Chroma  ──┐
Day30 增量    ├──► Day31 Hybrid ──► Day32 Rerank ──► Day33 Rewrite ──► Day36 Expansion
Day28 rebuild ──┘
```

---

## 迁移指南（Day33→34 发版）

1. 部署 v0.37.0 二进制/容器  
2. 首次启动自动 `RouteConfig()` 默认  
3. 跑 `pytest tests/day33 tests/day37`  
4. 抽样 chat citations 回归  
5. 前端确认 msg__route 渲染  

---

## 对照测验（自测 10 题）

1. Day33 核心类？ `RewritingRetriever`  
2. Day34 核心类？ `QueryRouter`  
3. Day34 默认 max_citations？ 3  
4. Day34 API 路径？ route-config  
5. 两者串联？ 是（改写后检索，再格式化引用）  
6. Day33 测试数？ 20  
7. Day34 测试数？ 20  
8. 关 citations 字段？ enabled=false  
9. rewrite 元数据？ include_route_meta  
10. 下一日？ HyDE 自适应路由
"""



def _file19() -> str:
    return f"""# 讲师补充阅读

## 1. Cross-Encoder 原文脉络

Reimers & Gurevych 指出 bi-encoder 适合召回，cross-encoder 适合 rewrite — 与本课三阶段一致。

## 2. Cohere Rerank API

商用 rerank 按 pair 计费；本课 mock 接口可无缝换 HTTP client。

## 3. latency 预算案例

某金融客服：pool=20、mock 10ms、真 BGE 80ms — 产品选 pool=15 折中。

## 4. 课堂彩蛋：Score calibration

检索分与展示 preview 独立；若要做 ensemble，须 Platt scaling 或 rank fusion。

## 5. 伦理与合规

引用展示提升可审计性 也可能把敏感段顶到首位 — 需内容策略与拒答规则配合。

## 6. 推荐阅读顺序

1. citation_builder.py  
2. context.py  
3. Day36 HyDE 预习  
"""


def _file20() -> str:
    return f"""# Day 37 完整代码走查

按**调用顺序**阅读，预计 90 分钟。精读全文见 `22_citation_builder精读.md`。

---

## 走查路线

| 顺序 | 文件 | 关注 |
|------|------|------|
| 1 | `citation_config.py` | validate / defaults |
| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |
| 3 | `context.py` | 三阶段 search |
| 4 | `knowledge_store.py` | _build_rag_service 外包 |
| 5 | `api/knowledge.py` | route-config |
| 6 | `day37/route_demo.py` | 开关对比 |
| 7 | `day37/route_api_demo.py` | TestClient |
| 8 | `tests/day37/` | 20 项 |

---

## 1. 配置层

`RouteConfig` 是改写单一真相源。store 启动 `from_dict` 加载；API PUT 更新。

**检查点**：默认 enabled=True, pool=20。

---

## 2. search 调用栈

```
POST /api/chat
  → RAGContextService.retrieve
    → DocumentIndex.search
      → RAGContextService.search
        → HybridRetriever.search(pool)
        → RuleBasedQueryRouter.route.rewrite
```

---

## 3. _build_rag_service

{fenced("python", _BUILD_RAG)}

**练习**：确认 `RAGContextService` 包裹 `HybridRetriever`，而非替换。

---

## 4. API 层

{fenced("python", _ROUTE_API)}

**检查点**：422 来自 `ValueError` → HTTPException。

---

## 5. route_demo

{fenced("python", ROUTE_DEMO)}

对每条 `ROUTE_QUERIES` 对比 enabled 开关。

---

## 6. 测试矩阵

| 文件 | 覆盖 |
|------|------|
| test_query_router.py | rewrite、翻牌、持久化、inner |
| test_route_api.py | HTTP、chat、version |

**必读**：`test_RuleBasedQueryRouter.route_from_results_candidates`、`test_citation_preview_with_rewrite`。

---

## 7. 走查后自测

1. 闭卷写出三阶段 search 5 步。  
2. 说明 rewrite 四项组成。  
3. 指出 PUT 后 chat 如何读到新 pool。

---

## 8. knowledge_store rewrite 节选

{fenced("python", _ROUTE_CFG_METHODS)}

---

## 9. 完整 citation_builder（走查用）

{fenced("python", QUERY_ROUTER)}

---

## 10. 走查时间盒（90 min 细分）

| 分钟 | 内容 |
|------|------|
| 0–15 | citation_config |
| 15–40 | citation_builder + rewrite |
| 40–55 | context |
| 55–70 | _build_rag_service + API |
| 70–90 | demos + tests |

---

## 11. 常见问题走查

**Q save 后 RAG 何时刷新？** `set_citation_config` → `invalidate_cache`。  
**Q enabled=False 还构造 citation_builder 吗？** 构造但不调用 rewrite。  

---

## 12. 走查验收 oral exam

学员随机抽：讲解 `test_RuleBasedQueryRouter.route_from_results_candidates` 如何构造噪声候选。
"""


def _file21() -> str:
    return f"""# Day 37 课堂知识竞赛（15 题）

1. 改写器类名？ → `RuleBasedQueryRouter.route`  
2. 管线类名？ → `RAGContextService`  
3. 默认 max_citations？ → `20`  
4. 默认 enabled？ → `True`  
5. 需求号？ → {REQ}  
6. 平台版本？ → {VER}  
7. route-config HTTP 方法？ → GET + PUT  
8. 打分函数？ → `rewrite`  
9. bigram 函数？ → `_bigram_overlap`  
10. inner 检索器？ → `HybridRetriever`  
11. 演示常量文件？ → `day37/constants.py`  
12. 测试总数？ → 18  
13. 精确子串得分？ → 1.0  
14. FR-007 实现？ → `_build_rag_service` 外包  
15. Day36 主题？ → query rewrite（自适应路由）  

---

## 抢答加分题（讲师用）

**16** 写出 pool 计算公式。  
**答**：`max(max_citations, top_k)`

**17** enabled=False 时 search 行为？  
**答**：`inner.search(query, top_k=top_k)` 直接返回

---

## 决赛三轮（讲师用）

**18** 默写 rewrite raw 公式。  
**19** 指出 route-config 两个路由 HTTP 方法。  
**20** 说明 `test_knowledge_store_persists_citation_config` 验证什么。

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

竞赛题 8（rewrite）正确率最低，下节课前抽查子串命中分支。
"""


def _file22() -> str:
    return f"""# Day 37 精读：answer_validator 与 Self-RAG 校验管线

**需求**：{REQ} | **学时**：120 min

---

## 一、citation_builder.py 全文

{fenced("python", QUERY_ROUTER)}

---

## 二、行级注释：QueryRouter 抽象（L18–L30）

| 行 | 讲解 |
|----|------|
| L18 | ABC 定义 `rewrite(query, candidates, top_k)` 接口 |
| L24–L30 | 返回重排后的 `RetrievalResult`，score 替换为 cross 分 |

---

## 三、RuleBasedQueryRouter.route（L33–L68）

{fenced("python", ROUTE_CONFIG)}

| 行 | 讲解 |
|----|------|
| L45–L48 | 空 query / 空候选早返回 |
| L50–L66 | 逐候选 `rewrite`，过滤 score≤0 |
| L68 | 按 score 降序 + chunk.index 稳定排序 |

---

## 四、rewrite 全文

{fenced("python", _ROUTE_CLASS)}

| 行 | 讲解 |
|----|------|
| 子串分支 | `q in t` → 1.0，电话/SKU 金路径 |
| coverage | matched tokens / query tokens |
| bigram_bonus | 连续二字共现比例 |
| length_penalty | 抑制长文噪声 |
| clamp | [0, 1] 便于 UI 展示 sim=% |

---

## 五、_bigram_overlap

{fenced("python", _ROUTE_CLASS)}

中文二字切分 + 英文词段，模拟 cross 细粒度交互。

---

## 六、context.py 全文

{fenced("python", CONTEXT_PY)}

---

## 七、search 主流程

{fenced("python", _ROUTING_SEARCH)}

| 行 | 讲解 |
|----|------|
| enabled=False | 委托 inner，零 rewrite 开销 |
| pool 计算 | `max(max_citations, top_k)` |
| candidates | inner hybrid 宽召回 |
| rewrite 调用 | MockCrossEncoder 改写截断 |

---

## 八、citation_config.py 全文

{fenced("python", ROUTE_CONFIG)}

`validate()`：pool ∈ [1,100]，model 仅 mock。

---

## 九、_build_rag_service 装配

{fenced("python", _BUILD_RAG)}

`RAGContextService(hybrid, ...)` — chat 无感知改写细节。

---

## 十、测试精读 test_query_router.py

{fenced("python", TEST_ROUTER)}

| 测试 | 要点 |
|------|------|
| test_RuleBasedQueryRouter.route_from_results_candidates | **翻牌金测** |
| test_rewrite_exact_substring | 子串=1.0 |
| test_citation_preview_with_rewrite | 业务号码 |
| test_context_disabled | 降级路径 |
| test_fetch_citations_with_hits_accessible | inner 类型 |
| test_knowledge_store_persists_citation_config | 持久化 |

---

## 十一、API 测试 test_route_api.py

{fenced("python", TEST_ROUTE_API)}

`test_health_version` 锁版本 `{VER}`；`test_chat_includes_citations` 端到端。

---

## 十二、调试清单

- [ ] 打印 candidates 前 5 的 hybrid score  
- [ ] 打印 rewrite 后前 3 的 rewrite  
- [ ] 切换 enabled 对比 top-1  
- [ ] 查 store.json citation_config  

---

## 十三、自检

1. 手绘三阶段 search 流程图。  
2. 口述 bi-encoder vs cross-encoder。  
3. 说明 length_penalty 作用。

---

## 十四、笔试模拟

**1（20分）** 构造反例：hybrid top-1 噪声、rewrite 翻牌。

**2（20分）** 解释 pool=10 vs 20 对 口语命中 与延迟影响。

**3（20分）** 对比 FR-002 与 FR-003 实现位置。

---

## 十五、与 Day33 衔接

HybridRetriever 仍是 inner；关 rewrite 即回 Day33 行为。retrieval_config 与 citation_config 正交。

---

## 十六、knowledge_store rewrite 方法

{fenced("python", _ROUTE_CFG_METHODS)}

`set_citation_config` 触发 `invalidate_cache`。

---

## 十七、口语考试题

1. 30 秒解释 rewrite 是什么。  
2. 1 分钟对比召回与改写。  
3. 白板画 RAGContextService.search。

---

## 十八、实验记录模板

| query | enabled | pool | top1_preview | top1_score |
|-------|---------|------|--------------|------------|
| | | | | |

---

## 十九、FAQ

**Q citations 与 context 重复吗？** 可优化；当前同步教学实现。  
**Q matched_tokens 来源？** 来自 RetrievalResult，展示在 Citation 中。  

---

## 二十、结课陈述

读罢 22 精读，你应能**逐行**解释 `RuleBasedQueryRouter.route` 与 `RoutingRetriever.search`，并映射到 {REQ} 的 FR-001–FR-003。

---

## 二十一、citation_builder 完整源码（重复嵌入便于打印）

{fenced("python", QUERY_ROUTER)}

---

## 二十二、自适应路由伪代码

```
function FETCH_CITATIONS(q, top_k):
    if not enabled: return INNER(q, top_k)
    P = max(max_citations, top_k)
    C = INNER(q, P)          # HybridRetriever
    return build_citation_bundle(q, C)
```

---

## 二十三、ROUTE_QUERIES 业务解读

| query | 业务意图 | citation 作用 |
|-------|----------|-------------|
| 年化收益率可达 | 产品收益 FAQ | 短句含 8% 顶上来 |
| 13900001111 | 查电话 | 子串 1.0 霸榜 |
| 投资有风险 | 合规披露 | 精确合规句优先 |

---

## 二十四、测试与 FR 映射

| 测试 | FR/NFR |
|------|--------|
| test_citation_config_validate | FR-004 |
| test_RuleBasedQueryRouter.route_from_results_candidates | FR-002 |
| test_context_enabled | FR-003 |
| test_citation_preview_with_rewrite | AC-03 |
| test_knowledge_store_persists_citation_config | FR-005 |
| test_health_version | FR-008 |
| test_put_citation_config_disable | AC-02 |
| test_chat_includes_citations | AC-05 |

---

## 二十五、knowledge API 节选（citation 上下文）

{fenced("python", KNOWLEDGE_API[:6000])}

---

## 二十六、phase3_route_review 建议

课后运行 `src/day37/phase3_route_review.py` 串联 Day25–34。

---

## 二十七、错题本

| 误区 | 正解 |
|------|------|
| citations 替代检索 | 展示层 |
| preview 与全文 | 截断展示 |
| PUT 不 save | API 内 save |

---

## 二十八、30 项自检（节选 20）

1. 能写 pool 公式  
2. 能写 rewrite 四项  
3. 能解释 enabled 分支  
4. 能定位 _build_rag_service  
5. 能 curl GET route-config  
6. 能 curl PUT 关 rewrite  
7. 能跑 route_demo  
8. 能跑 rewrite_api_demo  
9. 能数清 20 tests  
10. 能解释翻牌测试  
11. 能对比 Day33  
12. 能预告 Day36 HyDE  
13. 能读 validate 源码  
14. 能解释 include_route_meta  
15. 能解释 matched_tokens 保留  
16. 能解释 chunk.index tie-break  
17. 能解释 MODEL_MOCK  
18. 能解释 max_citations 上限 10  
19. 能解释 platform_version  
20. 能复述 {REQ} 目标  

---

## 二十九、延伸阅读：Retriever 组合模式

`fetch_citations` 是 **Facade**：对外返回 dict，对内调用 RoutingRetriever.search。与 Day33 Facade 叠加。

---

## 三十、完整测试文件（API）

{fenced("python", TEST_ROUTE_API)}

---

## 三十一、课堂录音稿（8 min）

「打开 context，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，citation_builder 逐对 rewrite，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」

---

## 三十二、Git 提交模板

```
feat(rag): cross-encoder rewrite pipeline (ZL-NA-REQ-032)

- RAGContextService + RouteConfig
- GET/PUT /api/knowledge/route-config
- tests/day37 (20 cases)
```

---

## 三十三、context 二次嵌入

{fenced("python", CONTEXT_PY)}

---

## 三十四、route_demo 全文

{fenced("python", ROUTE_DEMO)}

---

## 三十五、延迟估算习题

pool=20，单次 rewrite 0.5ms → rewrite 段约 10ms（不含 sort）。与 hybrid 45ms 合计 ~55ms 检索段。

---

## 三十六、口语命中 定义

离线标注集上，top-1 chunk 是否含期望 token（如 8%、号码）。rewrite 主要优化此指标。

---

## 三十七、与 ColBERT 边界

ColBERT late interaction 介于 bi 与 cross；本课不展开。

---

## 三十八、监控指标

`rag_citations_count`、`rag_citation_enabled`、`chat_with_citations_rate`。

---

## 三十九、Citation JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | int | 1-based 排序 |
| chunk_id | str | 可追溯分块 |
| source | str | 文档名 |
| score | float | rerank 后分数 |
| preview | str | 截断正文 |
| matched_tokens | list | 命中 token |

---

## 四十、citation_builder 全文嵌入

{fenced("python", QUERY_ROUTER)}

---

## 四十一、chat citations 代码

{fenced("python", _CHAT_CITATIONS)}

---

## 四十二、fetch_citations 代码

{fenced("python", _FETCH_CITATIONS)}

---

## 四十三、前端展示要点

`app.js` 的 `msg__route` 渲染 rank/source/score/preview；`msg__rewrite` 展示改写链。

---

## 四十四、合规场景

理财回答必须带风险提示引用 — citations 第一条应来自风险揭示 chunk。

---

## 四十五、测试与 FR 映射

| 测试 | FR |
|------|-----|
| test_RuleBasedQueryRouter.route_from_results | FR-002 |
| test_fetch_citations_with_hits | FR-003 |
| test_chat_includes_citations | FR-006 |
| test_citation_preview_with_rewrite | FR-005 |

---

## 四十六、完整 context.py 引用段

{fenced("python", _ROUTING_SEARCH)}

---

## 四十七、完整测试文件

{fenced("python", TEST_ROUTER)}

---

## 四十八、完整 API 测试

{fenced("python", TEST_ROUTE_API)}

---

## 四十九、课堂 8 分钟录音稿

「打开 citation_builder，Citation 有 rank chunk_id source score preview。chat 里 fetch_citations 挂在 reply 后面。前端 citations 数组渲染来源。这就是 ZL-NA-REQ-035。」

---

## 五十、End of 22 精读

**NexusAgent 课程 · Phase 3 · Day 37 · Citation · {REQ} · citation_builder 精读完**
"""


def _file23() -> str:
    return f"""# 候选池与延迟预算实践

## 实验 1：pool 扫描

```python
for pool in (10, 15, 20, 30, 40):
    store.set_citation_config(RouteConfig(enabled=True, max_citations=pool))
    # 对 ROUTE_QUERIES 打 口语命中 与计时
```

记录：pool≥20 后 口语命中 边际收益 <5%，延迟线性升。

## 实验 2：开关 A/B

同库同样 query，对比 enabled True/False 的 top-1 chunk_id。

## 实验 3：rewrite 消融

临时去掉 length_penalty，观察长文噪声是否回榜。

## 实验 4：子串金路径

query=`13900001111`，验证 rewrite=1.0 恒排第一。

## 实验 5：降级演练

PUT `enabled=false`，确认 P95 降、口语命中 可能降。

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

- 未 `set_citation_config` 后 `as_rag_service`  
- 忘记 `store.save()`  
- 用 hybrid score 评判 citation 展示 — 应看 source/preview  

---

## 实验 6：citation-preview vs chat

对同一 query 调 `POST citation-preview` 与 `POST /api/chat`，对比 citations 条数与 top1 source 是否一致。

---

## 实验 7：rewrite 元数据

`include_route_meta=false` 时 citation-preview 的 rewrite 字段应为 null。

---

## 实验 8：max_citations 扫描

```python
for n in (1, 2, 3, 5):
    store.set_citation_config(RouteConfig(max_citations=n))
    print(n, len(store.fetch_citations("年化收益率")["citations"]))
```

---

## 实验 9：前端验收

打开聊天页，发送「年化收益率是多少」，确认气泡下出现「引用来源」区块。

---

## 实验 10：合规审计表

| query | top1 source | 含风险词 | 合规 |
|-------|-------------|----------|------|
| 投资有风险吗 | | | |
| 年化收益 | | | |
"""


def _file24() -> str:
    return f"""# Phase 3 第十二日总结（Day 37）

## 本周进度

| Day | 主题 | 版本 |
|-----|------|------|
| 29 | Chroma | 0.29.x |
| 30 | 增量索引 | 0.30.x |
| 31 | 混合检索 | 0.31.x |
| 32 | Rerank | 0.32.x |
| 33 | Query Rewrite | 0.33.x |
| **34** | **Citation** | **{VER}** |

## Day 37 交付物

- QueryRouter + RouteConfig  
- route-config / citation-preview API  
- chat 响应 expansion.queries + merged citations + rewrite  
- 前端引用展示  
- 20 tests  
- 30 篇课件  

## 核心能力

**可解释性**：每条 RAG 回答可附带可追溯引用列表。

## 与 Phase 3 目标对齐

完整管线：rewrite → hybrid → rerank → **citations** → LLM。

## 学员自评 Rubric

| 等级 | 标准 |
|------|------|
| A | 能设计 Citation JSON + 写 chat 单测 |
| B | 能跑 route_demo 解释字段 |
| C | 能复述 citations 与 rewrite 关系 |
| D | 仅会 pytest -q |

## 下周预告

Day 37：HyDE / 自适应路由 — 一条问句变多条检索 query。

---

## Phase3 能力雷达（Day34 更新）

| 能力 | 等级 |
|------|------|
| 入库 | ★★★★★ |
| 召回 | ★★★★☆ |
| 精排 | ★★★★☆ |
| 改写 | ★★★★☆ |
| 溯源 | ★★★★☆ |
| 扩展 | ★★☆☆☆（Day36） |

---

## 团队复盘

1. citations 是否默认开启？  
2. preview 长度是否够用？  
3. 合规是否要求每条回答至少 1 条引用？  

---

## 金句墙

- 「有据可查」——陈默  
- 「chunk_id 是审计锚点」——林晓  
- 「reply 是面子，citations 是里子」——周航  

---

## 项目经理一页纸

{REQ} 已交付：QueryRouter、citation API、chat citations、前端展示、20 测试。下一步：Day36 多 query 扩展。
"""


def _file25() -> str:
    return f"""# route_api 脚本精读

## route_api_demo.py 全文

{fenced("python", ROUTE_API_DEMO)}

---

## 逐段讲解

| 行段 | 说明 |
|------|------|
| L13–L17 | 注入 `src` 与 `NEXUS_LLM_MOCK` |
| L21–L22 | TestClient 与 app |
| L26 | bootstrap 保证语料 |
| L30–L31 | GET 默认 rewrite 配置 |
| L33–L37 | PUT pool=20 — **API 核心演示** |
| L39–L40 | status 对账 citation_config |
| L42–L44 | chat + health version `{VER}` |

---

## route_demo.py 全文

{fenced("python", ROUTE_DEMO)}

`_top_hit` 切换 enabled 后 `as_rag_service()` — 注意缓存失效。

---

## constants.py

```python
ROUTE_QUERIES = (
    {{"query": "年化收益率可达", "expect_any": ("8%", "年化")}},
    {{"query": "13900001111", "expect_any": ("13900001111", "联系")}},
    {{"query": "投资有风险", "expect_any": ("风险", "谨慎")}},
)
```

---

## 运行矩阵

```bash
PYTHONPATH=src python3 src/day37/route_demo.py
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day37/route_api_demo.py
pytest tests/day37/test_route_api.py -v
```
"""


def _file26() -> str:
    return f"""# Day 37 实操 Lab 手册（Lab 0–7）

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Lab 0：环境自检（10 min）

```bash
python3 -c "import rag.citation_builder; print('ok')"
pytest tests/day37/ --collect-only -q
```

**通过标准**：collect ≥20 tests。

---

## Lab 1：读默认 citation 配置（15 min）

```bash
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.bootstrap_from_sample_docs()
print(s.get_citation_config().to_dict())
"
```

**通过标准**：`enabled=True`, `max_citations=3`。

---

## Lab 2：route_demo（25 min）

```bash
python3 src/day37/route_demo.py | tee /tmp/day37_demo.txt
```

**通过标准**：三条 Q；每条有 citations 列表；末尾 `✅`。

---

## Lab 3：citation-preview API（20 min）

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/citation-preview \\
  -H 'Content-Type: application/json' \\
  -d '{{"query":"那个理财能赚多少"}}' | jq .
```

**通过标准**：`citations` 非空；`rewrite.changed` 为 true。

---

## Lab 4：chat citations 对比（35 min）——必做

对「年化收益率是多少」「投资有风险吗」各发一条 chat，记录 `citations[0].source` 与 `preview` 前 40 字。

| query | citations 数 | top1 source | preview 摘要 |
|-------|--------------|-------------|--------------|
| | | | |
| | | | |

---

## Lab 5：API demo（20 min）

```bash
python3 src/day37/route_api_demo.py
```

**通过标准**：citation-preview 200；chat citations ≥1；version {VER}。

---

## Lab 6：关闭 citations（25 min）

```bash
curl -s -X PUT http://127.0.0.1:8000/api/knowledge/route-config \\
  -H 'Content-Type: application/json' \\
  -d '{{"enabled":false,"max_citations":3,"preview_max_chars":120,"include_route_meta":true}}'
```

再调 citation-preview，**通过标准**：`citations` 为空数组。

---

## Lab 7：全量回归（20 min）

```bash
pytest tests/day37/ -q
```

**通过标准**：20 passed。

---

## 提交

`lab/day37-<姓名>.md` 含 Lab 4 表格 + Lab 7 截图 + 前端 citations 截图。

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
| chat 无 citations | 查 citation_config.enabled |
| preview 空 | 换 query 或检查知识库 |
| 20 tests 失败 | 查 PYTHONPATH |

---

## 附录：20 项测试清单

| # | 测试 | 文件 |
|---|------|------|
| 1–11 | test_query_router.py | 单元 |
| 12–20 | test_route_api.py | API |

---

## 附录 B：Citation JSON 样例

```json
{{
  "rank": 1,
  "chunk_id": "raw_notice.txt-0",
  "source": "raw_notice.txt",
  "score": 0.92,
  "preview": "本产品年化收益率可达 8%...",
  "matched_tokens": ["年化", "收益"]
}}
```

---

## 附录 C：教师演示脚本

```python
from rag.knowledge_store import KnowledgeStore
store = KnowledgeStore.bootstrap_from_sample_docs()
for q in ("年化收益率", "那个理财能赚多少", "投资有风险"):
    d = store.fetch_citations(q)
    print(q, len(d["citations"]), d["citations"][0]["source"] if d["citations"] else "—")
```

---

## 附录 D：前端验收

打开静态页，确认 bot 气泡下出现灰色「引用来源」区块与改写斜体行。

---

## 附录 E：与 Day33 差异

| 项 | Day33 | Day34 |
|----|-------|-------|
| 核心 | rewrite query | 展示 citations |
| API | rewrite-preview | citation-preview |
| chat 字段 | 无 | expansion.queries + merged citations |
"""


def _file27() -> str:
    return f"""# Day 38 预习：多轮 Self-RAG 与重检索

**预告**：Day 37 单轮校验已能拒答，但部分场景应 **retry**（重检索 + 重生成）而非直接拒绝。

## 预习问

1. `retry_on_fail` 与 `refuse_on_fail` 如何共存？  
2. 重检索应放宽 route 还是强制 `rag_wide`？  

## Day38 路线图（预期）

| 模块 | 说明 |
|------|------|
| validation_retry.py | 校验失败 → 二次检索 |
| orchestrator 钩子 | 可选将 validate 下沉到编排层 |

## 一句话

Day37 让回答**可审计**；Day38 让失败**可恢复**。
"""



if __name__ == "__main__":
    write_course(37, build(), min_chars=100_000)
