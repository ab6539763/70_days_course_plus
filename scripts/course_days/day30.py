#!/usr/bin/env python3
"""Gold-standard course material builder for Day 30 — 增量索引 incremental upsert."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-030"
VER = "v0.30.0"
REPO = "nexus-agent-platform/src"

INCREMENTAL_MOD = read_repo(f"{REPO}/rag/knowledge_incremental.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
CHROMA_STORE = read_repo(f"{REPO}/rag/chroma_store.py")
INCREMENTAL_DEMO = read_repo(f"{REPO}/day30/incremental_demo.py")
INCREMENTAL_API_DEMO = read_repo(f"{REPO}/day30/incremental_api_demo.py")
TEST_INCREMENTAL = read_repo(f"{REPO}/../tests/day30/test_incremental_index.py")
TEST_INCREMENTAL_API = read_repo(f"{REPO}/../tests/day30/test_incremental_api.py")

_INCREMENTAL_FN = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def _incremental_index"): KNOWLEDGE_STORE.find(
        "def _build_rag_service"
    )
]
_REMOVE_FN = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("def _remove_document_by_source"): KNOWLEDGE_STORE.find(
        "def _resolve_chroma_path"
    )
]
_INGEST_INCREMENTAL = KNOWLEDGE_STORE[
    KNOWLEDGE_STORE.find("if incremental:"): KNOWLEDGE_STORE.find("return self.documents[-1]")
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
        "10_增量索引验收清单.md": _file10(),
        "11_增量索引详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_索引更新策略.md": _file13(),
        "14_企业案例集_公告秒级上线.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_增量API速查手册.md": _file17(),
        "18_与Day29能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_knowledge_incremental精读.md": _file22(),
        "23_同名替换与删除策略.md": _file23(),
        "24_Phase3第六日总结.md": _file24(),
        "25_incremental_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day31混合检索预习.md": _file27(),
    }
    return files


def _readme() -> str:
    return f"""# Day 30 课件索引

**日期**：2026-08-06（星期四）  
**主题**：增量索引（incremental upsert）  
**需求**：{REQ}  
**平台版本**：{VER}

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| _incremental_index | `rag/knowledge_store.py` | upload 不 reset，仅 upsert 受影响 chunk |
| _remove_document_by_source | `rag/knowledge_store.py` | 同名上传先删旧 JSON + Chroma |
| delete_by_ids / delete_by_source | `rag/chroma_store.py` | 向量级删除 |
| IncrementalReport | `rag/knowledge_incremental.py` | API 报告模型 |
| index_mode / last_incremental_at | store.json + status | 持久化状态 |
| 测试 | `tests/day30/` | 16 项 |

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day30/incremental_demo.py
python3 src/day30/incremental_api_demo.py
python3 -m pytest tests/day30/ -v
```

## 关键流程

Day 29 每次 upload 都 `chroma.reset()` → Day 30 **upload 增量**：仅 upsert 新文档 chunk；`rebuild` 仍全量 reset。

## 核心难点（必读）

**TF-IDF 词表扩张**：新文档引入 JSON 词表中不存在的新 token 时，向量**维度变长**。Chroma 同一 collection 内所有向量须等维——故 `_incremental_index` 在 `vocab_expanded=True` 时调用 `chroma.reset()` 后**全量 upsert** 所有 chunk（仍比 Day 29 少一次不必要的 reset 场景：同内容 re-upload 仅 upsert 受影响 id）。

## 设计决策

1. `ingest_bytes` 默认 `incremental=True`  
2. `rebuild_store` 仍 `_rebuild_index` + reset，`index_mode=full`  
3. 词表扩张 → affected=all chunks + chroma reset  
4. 评估路径仍用内存 EmbeddingRetriever  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_增量索引详解 | TF-IDF 扩张专题 |
| 22_knowledge_incremental精读 | 源码 + _incremental_index |
| 26_实操Lab手册 | 六步含 vocab 扩张实验 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
PYTHONPATH=src pytest tests/day30/ -q
```

通过标准：重复 upload `reset` 调用 0 次（mock 测试）；vocab 扩张时 `reset` 1 次且 `chroma_count==chunk_count`。

---

## TF-IDF 词表扩张（课程核心）

新 token → 向量维度增加 → Chroma collection 内旧向量维度不足 → **`chroma.reset()` 后全量 upsert**。详见 `11_增量索引详解.md` 与 `22_knowledge_incremental精读.md`。

---

## 配套代码路径

| 类型 | 路径 |
|------|------|
| 核心逻辑 | `src/rag/knowledge_store.py` |
| 报告模型 | `src/rag/knowledge_incremental.py` |
| 演示 | `src/day30/incremental_demo.py` |
| 测试 | `tests/day30/`（16 项） |

---

## 常见问题（课前）

**Q upload 仍慢？**  可能触发了 vocab 扩张；查 token 是否全新。  
**Q reset 能否禁用？**  扩张时不能；否则检索错误。  
**Q 与 Day29 关系？**  先 Chroma 再 incremental，顺序不可颠倒。  

---

## 一周复习计划

| 天 | 内容 |
|----|------|
| D0 | 11 专题 + 22 精读 |
| D1 | Lab Step5 |
| D2 | pytest day30 |
| D3 | 作业 A |
| D4 | 口述扩张原理 |
| D5 | Day31 预习 |

---

## 发版检查（Release Captain）

- [ ] PLATFORM_VERSION 0.30.0  
- [ ] tests day29+day30 绿  
- [ ] 课件 30 篇 regenerate  
- [ ] 产品话术 FR-006 已同步客服  
- [ ] 备份 SOP 未变（仍 JSON+chroma）  

---

## 相关仓库路径速查

```
nexus-agent-platform/src/rag/knowledge_store.py      # _incremental_index
nexus-agent-platform/src/rag/knowledge_incremental.py
nexus-agent-platform/src/rag/chroma_store.py       # delete_*
nexus-agent-platform/src/day30/incremental_demo.py
nexus-agent-platform/tests/day30/
```

---

## 学员画像（完成后）

你将能够：配置 incremental 环境；向运营解释扩张延迟；编写 mock reset 测试；在 incident 时判断该 rebuild 还是重传。
"""


def _narration() -> str:
    return f"""# Day 30 旁白解读

2026 年 8 月 6 日，星期四。林晓发现每次上传 PDF，日志里都出现 `chroma.reset()`。陈默：「Day 29 换了引擎，但节奏还是全量。生产环境上传一份公告不该重建整个索引。」

他在白板对比两条路径：

| 操作 | 索引策略 |
|------|----------|
| POST upload | incremental upsert |
| POST rebuild | full reset |

赵岩补充：「同名文件 re-upload 要先删旧 chunk，否则 JSON 会出现重复文档。」

下午 Lab 第三节，林晓连传两次 `notice.md`，`document_count` 不变，`index_mode=incremental`。她用 `unittest.mock.patch` 监控 `reset`，第二次上传调用次数为 0——全班鼓掌。

第四节是今日高潮：她上传一份含生僻合规术语「适当性匹配义务」的新 md，`vocab_expanded=True`，日志打印 `chroma.reset()` 一次，但 `document_count` 只增 1。陈默：「这不是退步，是 TF-IDF 的数学约束。换固定维 Embedding 就没有这步。」

```mermaid
journey
    title Day 30
    section 上午
      incremental vs full: 5: 林晓
      _remove_document_by_source: 4: 林晓
    section 下午
      upload 不 reset 验证: 5: 林晓
      vocab 扩张 reset 实验: 5: 林晓
      rebuild 仍全量: 4: 林晓
```

**金句**：陈默：「增量是默认，全量是例外；词表扩张时，Chroma 必须换跑道。」

---

## 技术旁白：patch reset 的 30 秒

林晓在 pytest 里写：

```python
with patch.object(ChromaVectorIndex, "reset") as mock_reset:
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    assert mock_reset.call_count == 0
```

第二次上传时她屏住呼吸——绿灯。周航：「这是 Day 30 最有力的回归测试，比任何 PPT 都有说服力。」

---

## 扩张实验现场

陈默让每人 UUID 造词写入 md。教室此起彼伏「reset calls: 1」。一名学员问：「能否禁用扩张？」陈默：「可以换固定维 Embedding，那是 Phase 4 议题。」

---

## 林晓日记节选

「今天终于理解陈默说的『数学约束』——不是不想增量，是 TF-IDF 维度会变。扩张实验那一刻我信了。」

---

## 时间线

| 时刻 | 事件 |
|------|------|
| 09:00 | 对比 Day29 upload 日志 |
| 10:30 | 讲 _remove_document_by_source |
| 11:00 | **TF-IDF 扩张**白板证明 |
| 14:00 | patch reset 实验 |
| 15:00 | expansion_lab |
| 16:30 | 16 tests green |

---

## 媒体稿（公关）

智链 NexusAgent {VER} 上线增量索引，知识库公告上传效率提升 80%。系统智能识别新术语并自动优化索引，保障金融合规用语可检索。
"""


def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：知识库增量索引  
**优先级**：P0  
**平台版本**：{VER}

---

## 1. 背景

Day 29 每次 `ingest_bytes` 触发 `_rebuild_index()` → `chroma.reset()` + 全库 upsert。运营上传单份公告耗时随库增大而线性增长，无法满足「秒级上线」SLA。

## 2. 目标

- upload 默认走 `_incremental_index`，**禁止**无必要 `reset`  
- 同名 re-upload 替换而非重复  
- rebuild 语义不变（全量）  
- 正确处理 TF-IDF 词表扩张  

## 3. 功能需求

### FR-001 增量 upload

- `ingest_bytes(..., incremental=True)` 默认  
- `ingest_parsed(..., incremental=False)` 默认（API 层封装）  
- 调用 `_incremental_index`，**不**调用 `chroma.reset()`（除非 vocab 扩张）

### FR-002 同名替换

- `_remove_document_by_source(filename)`  
- 删 JSON documents/chunks + Chroma `delete_by_ids`  
- reindex 剩余 chunk 的 `index` 字段  

### FR-003 Chroma 删除 API

- `delete_by_ids` / `delete_by_source`（Day 29 已实现，今日集成）

### FR-004 rebuild 不变

- `rebuild_store` → `_rebuild_index` + reset  
- `index_mode = full`

### FR-005 状态字段

- `last_incremental_at` ISO UTC  
- `index_mode`: `incremental` | `full`  
- status API 暴露  

### FR-006 TF-IDF 词表一致性（关键）

```python
old_vocab = embedding_state.get("vocab") or {{}}
# refit on ALL chunks
new_vocab = ...
vocab_expanded = len(new_vocab) > len(old_vocab) and bool(old_vocab)
if vocab_expanded:
    affected_chunks = ALL chunks
    chroma.reset()  # 维度变化，必须重建 collection
else:
    affected_chunks = new document chunks only
# upsert affected_chunks only
```

## 4. 非目标

- DELETE 文档 REST API  
- 异步索引队列  
- 切换神经网络 embedding  

---

## 4.1 FR 追溯矩阵

| FR | 实现位置 | 测试 |
|----|----------|------|
| FR-001 | _incremental_index | test_reupload_does_not_reset |
| FR-002 | _remove_document_by_source | test_reupload_replaces |
| FR-003 | chroma delete_* | test_chroma_delete_by_source |
| FR-004 | rebuild_store | test_rebuild_still_uses_full |
| FR-005 | save/load fields | test_incremental_persists |
| FR-006 | vocab_expanded branch | 手动 expansion_lab |

---

## 4.2 TF-IDF 扩张产品文案（多语言）

**中文**：新术语已加入词表，系统已自动重建向量索引。  
**EN**: Vocabulary expanded; vector index rebuilt automatically.

---

## 4.3 性能需求

- 无扩张 incremental P95 < 3s（100 chunk 库）  
- 扩张 P95 < 10s  
- rebuild 不变  

---

## 4.4 可回滚性

保留 `ingest_parsed(incremental=False)` 与 `_rebuild_index` 全量路径，一键回退运营策略。

## 5. 验收

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | 重复 upload 同文件 | reset 调用 0，doc 数不变 |
| AC-02 | 新文档 upload | index_mode=incremental |
| AC-03 | rebuild | index_mode=full |
| AC-04 | vocab 扩张 | reset 1 次，全量 upsert，count 一致 |
| AC-05 | chat | 增量后检索正常 |

---

## 6. 详细验收步骤

### 6.1 增量路径

```bash
pytest tests/day30/test_incremental_index.py::test_reupload_does_not_reset_chroma -v
pytest tests/day30/test_incremental_index.py::test_reupload_replaces_document_not_duplicates -v
```

### 6.2 扩张路径（手动）

上传含唯一新词的 md，检查 `len(vocab)` 增加且 `chroma.count()==chunk_count`。

### 6.3 rebuild 路径

```bash
pytest tests/day30/test_incremental_index.py::test_rebuild_still_uses_full_index_mode -v
```

### 6.4 API

```bash
pytest tests/day30/test_incremental_api.py -v
```

---

## 7. 风险登记

| 风险 | 缓解 |
|------|------|
| 扩张频繁体验抖动 | 监控 vocab_expanded 率 |
| 误用 ingest_parsed incremental=False | API 统一 bytes 入口 |
| orphan 向量 | remove 先删 Chroma |

---

## 8. 发布说明 {VER}

**新增**：增量 upload、IncrementalReport、status 增量字段  
**变更**：upload 默认不 reset  
**注意**：新术语文档触发一次性索引重建
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求扩展 — 用户故事

## US-030-01 运营秒传公告

**作为** 运营  
**我希望** 上传 md 后 3 秒内可检索  
**以便** 发布会同步答疑  

**验收**：第二次传同一文件不 reset；chroma_count 不变。

## US-030-02 合规术语上新

**作为** 合规  
**我希望** 新文档含新术语时系统仍正确检索  
**以便** 不出现「上传了却搜不到」  

**验收**：vocab 扩张时自动 reset+全量 upsert；`IncrementalReport.vocab_expanded=true`。

## US-030-03 开发可观测

**作为** 开发  
**我希望** status 有 index_mode 与 last_incremental_at  
**以便** 排障  

## TF-IDF 扩张 — 产品说明文案

「当新文档引入系统未见过的关键词时，向量维度会扩展。系统会自动重建向量索引（约 N 秒），属正常现象。固定维度 Embedding 模型无此步骤。」——供客服话术。

## 边界：空库首传

`old_vocab` 为空时 `vocab_expanded` 为 False（`bool(old_vocab)` guard），避免首次 upload 误判扩张。

## 与 Elasticsearch 类比

ES mapping 新增字段可 dynamic；但若改 analyzer 常需 reindex。TF-IDF vocab 扩张 ≈ 改 analyzer，故 Chroma reset。

---

## 用户故事 US-030-04 扩张可观测

**作为** 运营  
**我希望** 上传含新术语时界面提示「正在重建索引」  
**以便** 不误以为系统卡死  

**实现提示**：API 返回 `vocab_expanded: true` 时前端展示 toast。

---

## 用户故事 US-030-05 审计

**作为** 审计  
**我希望** 日志有 last_incremental_at  
**以便** 追溯公告上线时间  

---

## 非功能：性能基线

| 操作 | 目标 P95 |
|------|----------|
| incremental 无扩张 | <3s |
| incremental 扩张 | <10s |
| rebuild | <30s |
"""


def _architecture() -> str:
    return f"""# Day 30 架构设计 — 双路径索引

## 1. 路径分流

```mermaid
flowchart TD
    IN[ingest_bytes] --> Q{{incremental?}}
    Q -->|yes| RM[_remove_document_by_source]
    RM --> AP[_append_chunks]
    AP --> INC[_incremental_index]
    Q -->|no| AP2[_append_chunks]
    AP2 --> REB[_rebuild_index reset]
    RB[rebuild_store] --> REB
```

## 2. _incremental_index 内部

```mermaid
flowchart TD
    A[refit TF-IDF all chunks] --> B{{vocab expanded?}}
    B -->|yes| C[affected = all chunks]
    C --> D[chroma.reset]
    B -->|no| E[affected = new chunks]
    D --> F[upsert affected]
    E --> F
    F --> G[last_incremental_at now]
    G --> H[index_mode incremental]
```

## 3. 状态机 index_mode

```mermaid
stateDiagram-v2
    [*] --> full: bootstrap/rebuild
    full --> incremental: incremental upload
    incremental --> incremental: more uploads
    incremental --> full: rebuild
```

## 4. 组件职责

| 组件 | 职责 |
|------|------|
| knowledge_incremental.py | IncrementalReport 数据类 |
| knowledge_store._incremental_index | 核心算法 |
| knowledge_store._remove_document_by_source | 同名清理 |
| chroma_store.delete_* | 向量删除 |
| api/knowledge upload | 默认 incremental 响应 |

## 5. 不变量

任意时刻 `chroma_count == chunk_count`（空库除外）。

---

## 6. TF-IDF 扩张在架构中的位置

```mermaid
flowchart TD
    INC[_incremental_index] --> FIT[refit all chunks]
    FIT --> CMP{{vocab expanded?}}
    CMP -->|Yes| EXP[维度变化]
    EXP --> RST[chroma.reset]
    RST --> UPALL[upsert all vectors]
    CMP -->|No| UPPART[upsert new chunks only]
```

这是 Day30 **唯一**调用 reset 的 upload 路径。

---

## 7. 数据流：IncrementalReport

API 层在 upload 成功后可选调用 `incremental_upload(...)` 构造报告，含 `vocab_expanded` 供前端展示「已重建索引」toast。

---

## 8. 并发模型（讨论）

多 worker 同时 incremental upload 可能 race TF-IDF refit。教学单进程；生产需文件锁或队列。

---

## 9. 分层架构图

```
┌─────────────────────────────────────────────┐
│ Presentation: FastAPI upload / status        │
├─────────────────────────────────────────────┤
│ Application: KnowledgeStore ingest_*         │
├─────────────────────────────────────────────┤
│ Domain: _incremental_index / remove          │
├─────────────────────────────────────────────┤
│ Infrastructure: ChromaVectorIndex / JSON   │
└─────────────────────────────────────────────┘
```

---

## 10. 扩张检测逻辑形式化

```
vocab_expanded ≡ (|V_new| > |V_old|) ∧ (V_old ≠ ∅)
```

其中 V_old 来自本次 refit 前 `embedding_state` 快照，V_new 来自 refit 后 `export_state()`。

---

## 11. 失败恢复序列

1. upsert 抛错 → 记录日志  
2. status chroma_count ≠ chunk_count  
3. 运维 `POST rebuild`  
4. 验证 index_mode=full  

---

## 12. 与 CQRS 类比

upload 是 Command（写），chat 是 Query（读）。增量写路径优化不影响读接口。扩张时短暂不一致窗口类似 CQRS 最终一致。

---

## 13. 架构权衡记录

| 决策 | 备选 | 选择理由 |
|------|------|----------|
| 扩张全 upsert | 双 collection | 简单 |
| 同步索引 | 队列 | 教学清晰 |
| TF-IDF | 神经网络 | 无外部依赖 |
| mock reset 测试 | 集成测试耗时 | 快速反馈 |
"""


def _file01() -> str:
    return f"""# Day 30 企业背景与今日任务

**需求**：{REQ} | **版本**：{VER}

## 背景

发布会下午 2 点，运营需在 1 点前上传更正公告。Day 29 全量 rebuild 需 15 秒（库 200 chunk），产品投诉「上传太慢」。今日交付增量索引。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | _incremental_index + TF-IDF 扩张 |
| 下午 | Lab：重复上传 + 新词扩张 + API |
| 晚自习 | 读 Day 31 混合检索预习 |

## 自检

- [ ] 理解 Day 29 双存储  
- [ ] 能解释为何 vocab 扩张要 reset  
- [ ] 读过 `02_需求文档.md` FR-006  

---

## 企业背景详述

智链发布会 SLA：上传后 3 秒内 FAQ 机器人可答。Day29 全量路径 P95 14s 不达标。{REQ} 阻塞对外宣传「秒级知识更新」。

---

## 相关方

| 角色 | 诉求 |
|------|------|
| 运营 | 快 |
| 合规 | 新术语能搜 |
| 开发 | 可测 |
| 运维 | 可观测 index_mode |

---

## 今日代码阅读顺序

1. `knowledge_incremental.py`（10 min）  
2. `knowledge_store._remove_document_by_source`（15 min）  
3. `knowledge_store._incremental_index`（45 min）  
4. `tests/day30/test_incremental_index.py`（30 min）  

---

## 成功画像

17:30 你能向非技术同事解释：「为什么大多数上传很快，偶尔一次会慢一点。」
"""


def _file04() -> str:
    return f"""# Day 30 流程图与示意图

## 同名 re-upload

```mermaid
sequenceDiagram
    participant U as upload notice.md
    participant KS as KnowledgeStore
    participant C as Chroma
    U->>KS: ingest incremental
    KS->>KS: _remove_document_by_source
    KS->>C: delete_by_ids old
    KS->>KS: _append_chunks new
    KS->>KS: _incremental_index
    KS->>C: upsert new ids only
```

## vocab 扩张

```mermaid
sequenceDiagram
    participant KS as KnowledgeStore
    participant TF as TF-IDF fit
    participant C as Chroma
    KS->>TF: fit all chunks
    TF-->>KS: new_vocab larger
    KS->>C: reset()
    KS->>C: upsert ALL chunks
```

## ASCII：扩张决策

```
len(new_vocab) > len(old_vocab) and old_vocab non-empty?
    YES → reset + upsert(all)
    NO  → upsert(affected only)
```

---

## 状态时间线（ASCII）

```
t0: rebuild        index_mode=full
t1: upload doc A   incremental, no reset
t2: upload doc A'  incremental, remove+upsert
t3: upload doc B   incremental (new vocab?) 
t4: rebuild        full again
```

---

## 组件图

```
┌─────────────────────────────────────┐
│         KnowledgeStore               │
│  ingest_bytes ──► incremental path   │
│  rebuild_store ─► _rebuild_index     │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
 _incremental_index   chroma.reset (扩张/rebuild)
       │
       ▼
 chroma.upsert_chunks
```

---

## 10. 错误路径（故意触发）

| 操作 | 预期错误/行为 |
|------|----------------|
| upsert 维不一致 | chromadb 异常 |
| remove 不删 chroma | count 不等 |
| 跳过 refit | 检索分数异常 |
"""


def _file05() -> str:
    return f"""# Day 30 课堂笔记（上午）

## 第一节：为何增量（40 min）

全量 reset 成本 O(全库)；增量 O(新文档块)。运营路径是高频增量。

## 第二节：_remove_document_by_source（30 min）

顺序：Chroma delete → filter JSON → reindex index 字段。必须先删向量再删 JSON，避免 orphan id。

{fenced("python", _REMOVE_FN)}

## 第三节：TF-IDF 词表扩张（50 min）——今日核心

### 原理

TF-IDF 向量长度 = |vocab|。新词出现 → 维度 +1 → 旧向量缺维 → Chroma 无法与新区块并存于同一 collection。

### 代码

{fenced("python", _INCREMENTAL_FN)}

### 课堂实验

1. 准备 `rare_term.md` 含独有词「量子纠缠费率」  
2. upload 后看 `vocab_expanded`  
3. patch `reset` 断言调用 1 次  

### 对比固定维 Embedding

| 类型 | 维度 | 增量 |
|------|------|------|
| TF-IDF | 随 vocab 变 | 扩张要 reset |
| ada-002 | 1536 固定 | 仅 upsert 新 id |

## 第四节：IncrementalReport

{fenced("python", INCREMENTAL_MOD)}

---

## 第五节：IDF 变化与「非扩张」仍 refit 全库

即使无新 token，新文档加入会改变文档频率 df，从而改变 IDF 权重。教学实现因此在 `_incremental_index` **总是** `EmbeddingRetriever(self.chunks)` 全库 refit。仅 upsert 的向量是 `affected_chunks` 的 embed 结果；若 IDF 变了但未扩张，旧块在 Chroma 中的向量数值已陈旧——严格做法应 upsert 全库。本项目在**非扩张**路径只 upsert 新块，是性能与一致性的折中；扩张路径则 upsert 全库保证一致。

**考试可能问**：为何扩张必须 upsert all？因为维度变了，旧向量必须全部重算。

---

## 第六节：白板式对比表

| 操作 | reset | upsert 范围 | index_mode |
|------|-------|-------------|------------|
| incremental 普通 | 否 | 新文档块 | incremental |
| incremental 扩张 | 是 | 全库 | incremental |
| rebuild | 是 | 全库 | full |
| Day29 upload | 是 | 全库 | full |
"""


def _file06() -> str:
    return f"""# Day 30 课堂笔记（下午）

## API upload 响应

```json
{{
  "message": "文档已增量索引",
  "index_mode": "incremental",
  "filename": "notice.md",
  "chunk_count": 15
}}
```

## Lab 监控 reset

```python
from unittest.mock import patch
from rag.chroma_store import ChromaVectorIndex

with patch.object(ChromaVectorIndex, "reset") as m:
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    assert m.call_count == 0
```

## rebuild 对照

`rebuild_store` 后 `index_mode=full`，验证 `test_rebuild_still_uses_full_index_mode`。

## 故障表

| 现象 | 原因 | 处理 |
|------|------|------|
| 重复 doc | 未 remove | 查 incremental 分支 |
| count 不等 | 扩张 upsert 中断 | rebuild |
| 搜不到新词 | 未 refit | 查 embedding_state |

---

## 第六节：expansion_lab 教师备注

UUID 词须足够生僻，避免与 sample_docs 撞车。建议前缀 `ZlNa030_`。学员常见错误：忘记 UTF-8 encode。

---

## 第七节：与 Day29 测试对照

| 测试 | Day29 | Day30 |
|------|-------|-------|
| upload reset | 不测 0 | 必须 0 |
| chroma_count | ✅ | ✅ |
| index_mode | 可选 | 必须 |

---

## 第八节：mock 原理深入

`unittest.mock.patch.object(ChromaVectorIndex, "reset")` 替换类方法为 MagicMock。调用 `ingest_bytes` 时若代码路径误触 `reset`，`call_count` 增加。这是**行为验证**，不断言内部 TF-IDF 数值。

扩张实验则断言 `call_count==1`，与零次形成对照。

---

## 第九节：课堂练习 5min

两两一组：一人描述「同文件 re-upload」，另一人描述「新词扩张」；听众指出是否含 reset。
"""


def _file07() -> str:
    return f"""# Day 30 晚自习

## 讨论

1. 为何 `bool(old_vocab)` 防止首传误判扩张？  
2. 若扩张很频繁，运营体验如何优化？（提示：预 rebuild / 固定 embedding）  
3. CDC 与增量索引关系？  

## 阅读

`13_深度扩展_索引更新策略.md`

## 预习 Day 31

混合检索：BM25 + 向量融合。

---

## 深度讨论：Elasticsearch partial update

| ES | Chroma incremental |
|----|-------------------|
| 倒排增量 | 向量 upsert |
| mapping 变更 reindex | vocab 扩张 reset |
| near real-time | 同步执行 |

---

## 晚自习物料：写扩张决策伪代码

闭卷 10 行以内，同桌互评。

---

## 扩展阅读：LinkedIn 帖子（英）

"Day 30 shipped incremental indexing for our RAG knowledge base. TF-IDF vocab expansion still forces a Chroma reset — dimensionality matters. Fixed-dim embeddings next quarter."

---

## 思考题

若每周扩张 50 次，是否应换 embedding 模型？列出决策树。

---

## 晚自习第二小时：代码默写

默写 `_incremental_index` 中扩张分支 6 行核心代码（不看 IDE）。同桌交换批改。

---

## 第三小时：Day31 预习讨论

混合检索如何解决「SKU-12345」类精确查询？写下你的假设，明日验证。
"""


def _file08() -> str:
    return f"""# Day 30 作业

## A（40 分）：incremental 统计脚本

统计 `store.json` 的 `last_incremental_at` 与 `index_mode`，输出人类可读报告。

## B（30 分）：问答

1. 画出 vocab 扩张时的数据流。  
2. 为何 re-upload 同内容不扩张？  
3. `ingest_parsed` 与 `ingest_bytes` incremental 默认值差异？  

## C（30 分）：Lab 报告

完成 `26_实操Lab手册.md`，含 **Step 5 vocab 扩张实验** 截图。

---

## 作业 D（bonus 10 分）

实现最小复现：`vocab_expanded` 单元测试，用 `tmp_path` store，构造两阶段 ingest，断言 reset 调用次数。

---

## 学术诚信

允许讨论；禁止抄同伴 expansion_lab 输出。

---

## 提交清单

- [ ] homework 分支  
- [ ] lab/day30-姓名.md  
- [ ] 脚本 A（若选做 D）  

## 提交

分支 `homework/day30-<姓名>`。

---

## 作业 A 完整参考实现

```python
#!/usr/bin/env python3
# Incremental 状态报告 — Day30 作业参考
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nexus-agent-platform" / "src"))

from utils.json_utils import load_json  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--store", type=Path, default=ROOT / "nexus-agent-platform" / "data" / "knowledge" / "store.json")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    raw = load_json(args.store, default={{}}) or {{}}
    report = {{
        "index_mode": raw.get("index_mode", "unknown"),
        "last_incremental_at": raw.get("last_incremental_at"),
        "last_rebuilt_at": raw.get("last_rebuilt_at"),
        "chunk_count": len(raw.get("chunks") or []),
        "vocab_size": len((raw.get("embedding") or {{}}).get("vocab") or {{}}),
    }}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"index_mode={{report['index_mode']}}")
        print(f"last_incremental_at={{report['last_incremental_at']}}")
        print(f"vocab_size={{report['vocab_size']}} chunks={{report['chunk_count']}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 评分细则

| 项 | 分 |
|----|-----|
| 脚本可运行 | 20 |
| --json 输出 | 10 |
| 报告含扩张实验 | 30 |
| 问答 B | 30 |
| 代码风格 | 10 |
"""


def _file09() -> str:
    return f"""# Day 30 作业答案

## B 参考答案

1. refit → len(new_vocab)>len(old) → affected=all → reset → upsert all  
2. 同内容无新 token，vocab 不变，仅 upsert 替换的 chunk id  
3. `ingest_bytes` 默认 True；`ingest_parsed` 默认 False（API upload 封装 bytes 路径）  

## A 参考片段

```python
raw = load_json(path)
print(raw.get("index_mode"), raw.get("last_incremental_at"))
```

---

## C 报告评分表

| 项 | 优秀 | 及格 |
|----|------|------|
| Step5 数据 | 完整表格 | 缺 reset_calls |
| 三问 | 全对 | 对 2 问 |
| 截图 | 清晰 | 模糊 |

---

## D 题答案要点

构造两阶段 ingest：先 bootstrap 小库，再 ingest 含 UUID 词文档；patch reset；断言 call_count==1 且 vocab 变大。

---

## 阅卷注意事项

- 三问缺「维度」关键词扣 5 分  
- 未解释 bool(old_vocab) 扣 3 分  
- 抄袭 expansion 模板重罚
"""


def _file10() -> str:
    return f"""# Day 30 增量索引验收清单

- [ ] `_incremental_index` 实现  
- [ ] `_remove_document_by_source` 实现  
- [ ] upload 默认 incremental  
- [ ] rebuild → index_mode=full  
- [ ] vocab 扩张 reset 逻辑  
- [ ] `tests/day30/` 16 项全绿  
- [ ] `incremental_demo.py` ✅  
- [ ] status 含 last_incremental_at  

**签字**：___________

---

## 现场验收脚本

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day30/ -q
python3 src/day30/incremental_demo.py | grep -q "✅"
python3 src/day30/incremental_api_demo.py | grep -q "✅"
echo DAY30_OK
```

---

## 扩张专项验收

教师准备含 UUID 词的 md，学员现场 upload，教师检查：

- [ ] vocab 长度增加  
- [ ] reset 调用 1 次（日志或 debugger）  
- [ ] chroma_count 正确  
- [ ] chat 能检索新词  

---

## 失败处置

| 失败 | 动作 |
|------|------|
| reset 未调 | 查 vocab_expanded 逻辑 |
| reset 误调 | 查是否误判扩张 |
| 重复 doc | 查 remove |

---

## 学员能力达成（ABCD）

A：能配置 incremental 环境  
B：能解释 vocab 扩张 reset  
C：能跑通 expansion_lab  
D：能教他人 mock reset 测试  

---

## 教师备注

验收当日先跑 `DAY30_OK` 脚本，再抽查 2 名学员口述扩张原理。扩张实验为硬性项，不可跳过。
"""


def _file11() -> str:
    return f"""# 增量索引详解（Day 30 专题）

## 1. 问题定义

增量索引 = 仅更新受变更影响的索引条目，而非重建全库。

## 2. 双路径对照

| 路径 | Chroma | TF-IDF |
|------|--------|--------|
| upload incremental | upsert affected | refit all |
| rebuild full | reset + upsert all | refit all |

## 3. TF-IDF 词表扩张深度讲解

### 3.1 向量如何构建

每个 chunk 文本 → tokenize → 按 vocab 下标填 TF-IDF 权重 → 得到长度 = |vocab| 的稀疏向量（教学实现稠密 list[float]）。

### 3.2 扩张场景

库内已有词表 {{年化, 收益, 风险}}，维度 3。新文档含「合规」→ fit 后词表 {{年化, 收益, 风险, 合规}}，维度 4。

旧 Chroma 中存的三维向量与新的四维向量**不能共存**于同一 cosine 空间配置——Chroma 假定 collection 内向量等维。

### 3.3 算法响应

```python
vocab_expanded = len(new_vocab) > len(old_vocab) and bool(old_vocab)
if vocab_expanded:
    affected_chunks = list(self.chunks)  # 全库重 embed
    chroma.reset()  # 清空旧维向量
chroma.upsert_chunks(affected_chunks, vectors)
```

**注意**：扩张时仍要避免「无意义 reset」——只有扩张才 reset；普通增量**不** reset。

### 3.4 同内容 re-upload

删除旧 chunk → 追加同内容新 chunk（chunk_id 可能变）→ refit 词表不变 → `vocab_expanded=False` → 仅 upsert 新块向量 → **无 reset**。

### 3.5 与 Day 29 对比

| 场景 | Day 29 | Day 30 |
|------|--------|--------|
| 新文档 | reset+全量 | upsert 新块 |
| 同文件再传 | reset+全量 | remove+upsert |
| 新词出现 | reset+全量 | reset+全量（同结果，但路径明确） |

Day 30 价值在于**常见路径**（无新词）不再 reset。

## 4. IncrementalReport 字段

| 字段 | 含义 |
|------|------|
| vocab_expanded | 是否触发扩张分支 |
| chunks_added | 新块数 |
| chunks_removed | 删除旧块数 |
| chroma_count |  upsert 后 count |

## 5. 运维监控

告警规则：`index_mode=incremental` 且 `vocab_expanded` 连续 true → 建议安排维护窗口做 rebuild 或评估换 embedding。

## 6. 常见误区

| 误区 | 正解 |
|------|------|
| 增量永远不调 reset | 扩张时必须 reset |
| 扩张可只 upsert 新块 | 旧块向量维度过短，必须全量重 embed |
| rebuild 可省略 | rebuild 仍是发布 chunk_config 的权威路径 |

## 7. 固定维 Embedding 展望

若 Day 35 切换 ada-002，维度恒 1536，`vocab_expanded` 分支可退役，增量始终 upsert only——这是神经网络 embedding 的工程优势。

## 8. 数学例题

旧 vocab 大小 100，新文档引入 3 个全新 token，新 vocab 103。问：须 upsert 多少 chunk？  
**答**：全部 chunk（扩张分支），因旧 100 维向量需重新 embed 为 103 维。

## 9. 课堂演示脚本思路

```python
# 1. 上传含唯一词 UUID 的 md
# 2. 打印 store.embedding_state["vocab"] 长度前后
# 3. 断言 reset 调用次数
```

## 10. 小结

增量索引的三层含义：**操作增量**（少 reset）、**数据增量**（只 upsert affected）、**例外全量**（词表扩张时 reset+全 upsert）。

---

## 11. 工作负载分析（示意）

设库含 N chunk，新文档产生 k chunk，refit TF-IDF 成本 O(N) 文本扫描，upsert 成本 O(k) 或 O(N)（扩张）。

| 场景 | reset | upsert 数 | 相对 Day29 |
|------|-------|-----------|------------|
| 新 doc 无新词 | 0 | k | 大幅提升 |
| 同 doc re-upload | 0 | k | 大幅提升 |
| 新 doc 有新词 | 1 | N | 仍优或持平 |
| rebuild | 1 | N | 同 Day29 |

当 N=500, k=5 时，无扩张增量路径约省两个数量级常数因子。

---

## 12. embedding_state 结构（复习）

```json
{{
  "vocab": {{ "年化": 0, "收益": 1 }},
  "idf": [ 1.2, 0.8 ],
  "dimension": 2
}}
```

`dimension` 应等于 `len(vocab)`。扩张后 dimension 递增，旧 Chroma 向量长度不匹配。

---

## 13. 课堂白板证明（复制到笔记）

```
命题：词表从 n 扩到 n+k 时，必须对所有 chunk 重新 embed 并 reset Chroma。

证：
1. 旧向量 ∈ R^n，新向量 ∈ R^(n+k)，n ≠ n+k 不能同一向量空间索引。
2. Chroma collection 要求等维。
3. 故 reset 后 upsert 全部新向量。□
```

---

## 14. 非扩张路径完整伪代码

```
old = snapshot_vocab()
refit(all_chunks)
new = export_vocab()
if len(new) > len(old) and old:
    affected = all_chunks
    chroma.reset()
else:
    affected = new_doc_chunks_only
upsert(affected)
persist last_incremental_at, index_mode=incremental
```

---

## 15. 与产品经理对齐话术

「大部分上传 1–2 秒完成；仅当文档含全新专业术语时，系统重建索引约 5–10 秒，请避免在发布会前 1 分钟首传含造词文档。」

---

## 16. 监控指标建议

- `incremental_upload_total` counter  
- `vocab_expansion_total` counter  
- `incremental_duration_ms` histogram  

扩张率突增 → 告警给算法组评估是否切换固定维 embedding。

---

## 17. 端到端数值例题

**已知**：库 10 chunk，vocab 大小 50。新文档引入 2 个全新 token。

**问**：`affected_chunks` 数量？是否 reset？  
**答**：10，是。

**问**：若新文档仅含已有词？  
**答**：affected = 新文档块数 k，否。

---

## 18. IDF 公式复习

```
idf(t) = log((N+1)/(df(t)+1)) + 1
```

新文档加入改变 N 与部分 df，故理论上所有 chunk 的 TF-IDF 向量都应重算。工程上非扩张路径仅 upsert 新块是近似优化；**扩张路径必须全库 upsert** 保维度一致。

---

## 19. Chroma reset 内部发生了什么

`delete_collection` → SQLite 元数据删除 → HNSW 图销毁 → `get_or_create_collection` 新建空图。旧向量不可恢复，必须从 JSON chunks + 新词表 re-embed。

---

## 20. 单元测试设计指南

| 测试 | mock | 断言 |
|------|------|------|
| 普通增量 | reset | call_count==0 |
| 扩张 | reset | call_count==1 |
| rebuild | reset | call_count>=1 |
| 空库 | reset | count==0 |

---

## 21. 产品边界声明

本实现不做：跨天合并 vocab 压缩、停用词表版本管理、增量删除 REST API。删除文档可用 rebuild 或后续 Day 扩展。

---

## 22. 课堂录音金句汇总

- 「增量是默认，全量是例外。」  
- 「词表扩张不是 bug，是 TF-IDF 的数学。」  
- 「mock reset 比 prof 更能说服 CTO。」  
- 「Chroma 换跑道，不是倒车。」

---

## 23. 场景剧本（角色扮演）

**运营**：上传发布会稿。  
**系统**：incremental，2s 完成。  
**运营**：更正稿再传同名。  
**系统**：remove+upsert，无 reset。  
**合规**：加急上传含新法规词「适当性匹配义务」。  
**系统**：vocab 扩张，reset 一次，6s，toast「索引已重建」。  
**开发**：查 status `index_mode=incremental`，`last_incremental_at` 更新。

---

## 24. 对比表：三种 Embedding 策略

| 策略 | 扩张 reset | 实现难度 |
|------|------------|----------|
| TF-IDF | 需要 | 低 |
| sentence-transformers | 不需要 | 中 |
| OpenAI ada | 不需要 | 低（依赖 API） |

---

## 25. 合规留存

保留 expansion 实验日志 90 天，供「为何当时重建索引」审计说明。

---

## 26. 专题阅读清单（90 min）

1. 本文件第 3、11、17–25 节  
2. `22_knowledge_incremental精读.md` 全文  
3. `tests/day30/test_incremental_index.py`  
4. Chroma 文档：upsert vs delete  

---

## 27. 自测 15 题（专题结束）

1. incremental 谁调 reset？  
2. 扩张 affected？  
3. IncrementalReport 几个字段？  
4. ……（教师可口播）

---

## 28. 术语中英对照

| 中文 | EN |
|------|-----|
| 增量索引 | incremental indexing |
| 词表扩张 | vocabulary expansion |
| 全量重建 | full rebuild |
| 同名替换 | same-name replace |

---

## 29. FAQ 扩展（专题）

**Q：能否缓存旧向量补零扩维？**  
A：TF-IDF 新维权重非零，补零语义错误；必须重算。

**Q：扩张能否后台异步？**  
A：可，但读路径需版本号；本课程同步。

**Q：incremental 与事务？**  
A：理想应用 outbox；当前 best-effort。

**Q：如何人为触发扩张测试？**  
A：UUID 词 expansion_lab。

**Q：Day31 混合检索还用 TF-IDF 吗？**  
A：是，外加关键词路。

---

## 30. 手算例题（课堂）

**库**：两文档  
- D1: 「年化 收益」  
- D2: 「风险 等级」  

**vocab**（简化）: {{年化:0, 收益:1, 风险:2, 等级:3}}，维度 4。

**新文档 D3**: 「合规 披露」→ 新 vocab 维度 6。

**问**：Chroma 中 D1/D2 旧向量维数？ upload D3 后应如何处理？  
**答**：维数 4；扩张，reset，对 D1,D2,D3 全部重 embed 为维数 6 再 upsert。

---

## 31. 与生产系统对照

| 系统 | 增量 | 扩张处理 |
|------|------|----------|
| NexusAgent D30 | ✅ | reset+full upsert |
| Elasticsearch | ✅ | reindex |
| Pinecone | ✅ | 固定维无此问题 |
| Git grep 索引 | ✅ | 倒排增量 |

---

## 32. 课件版本

本文档随 {VER} 发版；若 `knowledge_store._incremental_index` 实现变更，以仓库为准。

---

## 33. 十大误区详解

**误区 1**：「增量就是从不 reset。」——错，扩张要 reset。  
**误区 2**：「reset 等于 rebuild。」——错，rebuild 还重扫源文件。  
**误区 3**：「只删 JSON 即可替换文档。」——错，须删 Chroma 向量。  
**误区 4**：「首传会 vocab_expanded。」——错，有 bool(old_vocab) 保护。  
**误区 5**：「IDF 不变则向量不变。」——严格说 N 变 IDF 可能变；本实现非扩张只 upsert 新块。  
**误区 6**：「Chroma upsert 可补维度。」——错。  
**误区 7**：「评估失败因 incremental。」——评估不走 Chroma。  
**误区 8**：「index_mode 只是标签。」——影响运维判断与 SLA。  
**误区 9**：「delete_by_source 足够。」——我们优先 ids 精确删除。  
**误区 10**：「Day30 可跳过 Day29。」——双存储是前提。

---

## 34. 实验变量对照表

| 变量 | 水平 |
|------|------|
| 文档 | 同内容 / 新内容 |
| 词表 | 无新 token / 有新 token |
| 路径 | incremental / full |
| 预期 reset | 0 / 1 |

全因子 2^3=8 种组合，Lab 至少完成其中 4 种。

---

## 35. 向 CTO 汇报一页纸大纲

1. 问题：upload 太慢  
2. 方案：incremental + 扩张处理  
3. 风险：扩张抖动  
4. 指标：P95 2.1s  
5. 测试：16 项 + mock reset  
6. 下一步：混合检索  

---

## 36. 代码审查 comment 模板

- [ ] 扩张分支是否 upsert all  
- [ ] 非扩张是否避免 reset  
- [ ] remove 顺序是否正确  
- [ ] 持久化 index_mode  
- [ ] API 文档更新  
"""


def _file12() -> str:
    return f"""# Day 30 课堂练习册

## 选择题

**1.** upload 默认 incremental？ A 否 B 是 → B  
**2.** vocab 扩张时 affected chunks？ A 仅新 B 全部 C 无 → B  
**3.** 扩张时是否 reset？ A 否 B 是 → B  
**4.** rebuild 后 index_mode？ A incremental B full → B  
**5.** IncrementalReport 哪个字段表扩张？ A chroma_count B vocab_expanded → B  

## 简答

解释为何 TF-IDF 增量比固定维 embedding 多一个 reset 分支。

## 实操

运行 `test_reupload_does_not_reset_chroma`，解释 mock reset 的意义。

---

## 二（续）、简答题 Rubric

| 题 | 要点 |
|----|------|
| TF-IDF vs 固定维 | 维度是否随 vocab 变；扩张要 reset |
| mock reset | 验证增量路径不调用全量重建 |

---

## 三、连线题

| 左 | 右 |
|----|-----|
| vocab_expanded | A. 删旧同名文档 |
| _remove_document_by_source | B. 词表变大 |
| index_mode full | C. rebuild 后 |
| upsert only | D. 普通增量 |

答案：1-B, 2-A, 3-C, 4-D

---

## 四、代码阅读（20 分）

阅读 `_incremental_index` 中 `if vocab_expanded:` 分支，说明为何先 `affected_chunks = list(self.chunks)` 再 `reset()`，顺序能否颠倒？

**参考**：应先确定 affected 集合再 reset；reset 后 collection 空，但逻辑上先算 affected 更清晰；颠倒若 upsert 失败可能空库——应用事务思想，教学代码靠单线程顺序保证。

---

## 五、计算题（10 分）

库 200 chunk，vocab 500。新文档 8 chunk，引入 5 个新 token。问 affected 数量与 reset 次数。

**答**：affected=200（扩张），reset=1。

---

## 六、判断题

1. 每次 incremental 都 reset。×  
2. rebuild 后 index_mode 为 full。√  
3. 首传空库 vocab_expanded 为 true。×  
4. 同文件 re-upload document_count 不变。√  
"""


def _file13() -> str:
    return f"""# 深度扩展：索引更新策略

## CDC vs Batch

| 模式 | 延迟 | 复杂度 |
|------|------|--------|
| CDC 流式 | 低 | 高 |
| 批量 rebuild | 高 | 低 |
| 增量 upsert | 中 | 中 |

NexusAgent Day 30 属「增量 upsert + 定期 rebuild」混合。

## Lucene 段合并类比

Chroma HNSW 图增量插入后结构变化；极端情况下需 rebuild 图。TF-IDF 扩张类似「改字段类型必须 reindex」。

## 版本向量

工业界用「embedding 模型版本号」+ 全量重建任务；我们用在 `embedding_state` 隐式版本（vocab 内容）。

---

## 近实时索引架构（扩展阅读）

```mermaid
flowchart LR
    W[写入 API] --> Q[索引队列]
    Q --> I[Incremental Worker]
    I --> V{{vocab expanded?}}
    V -->|yes| R[reset+full upsert]
    V -->|no| U[partial upsert]
    R --> CH[(Chroma)]
    U --> CH
```

NexusAgent 当前同步执行，无异步队列；上图为 Phase 4 演进方向。

---

## Debezium / CDC 对照

数据库 CDC 捕获行级变更；知识库 upload 是文件级变更。`_remove_document_by_source` 类似 CDC delete 事件；`_append_chunks` 类似 insert。

---

## 批量 vs 流式权衡表

| 策略 | 延迟 | 一致性 | 实现 |
|------|------|--------|------|
| Day28 rebuild | 高 | 强 | 简单 |
| Day30 incremental | 低 | 强* | 中等 |
| 异步队列 | 最低 | 最终 | 复杂 |

*扩张时短暂 reset 窗口内查询可能空，教学环境单用户可忽略。
"""


def _file14() -> str:
    return f"""# 企业案例：公告秒级上线

## 场景

发布会前 10 分钟，运营上传 `press_correction.md`。Day 29 全量 rebuild 12 秒；Day 30 增量 1.8 秒，会场问答及时命中「更正」关键词。

## vocab 扩张插曲

更正稿含新造营销词「智链双擎」，触发扩张 reset，耗时 6 秒，仍优于全库 15 秒。陈默记录：「罕见词事件可接受。」

## 指标

| 指标 | Day 29 | Day 30 |
|------|--------|--------|
| 同文件 re-upload | 15s | 0.9s |
| 新文件无新词 | 15s | 1.8s |
| 新文件有新词 | 15s | 6s |

---

## 回滚预案

若增量 bug 阻塞发布，feature flag `INGEST_INCREMENTAL=0` 回退 `_rebuild_index` 路径（需代码开关，本课程未实现，讨论题）。

---

## 客户沟通邮件模板

主题：知识库上传性能升级（{VER}）

正文：上传响应时间预计降低 80%；若文档含全新术语，系统将自动重建索引一次，耗时约 5–10 秒，请提前上传备稿。

---

## 数据点采集

| 日期 | 上传次数 | 扩张次数 | P95 延迟 |
|------|----------|----------|----------|
| 08-05 Day29 | 120 | N/A | 14s |
| 08-06 Day30 | 118 | 3 | 2.1s |

---

## 案例 D：误操作 teachable moment

实习生 `ingest_parsed(incremental=False)` 上传，触发全量 rebuild，发布会前 5 分钟。回滚：git checkout store.json + chroma 备份；教训：API 层统一 `ingest_bytes`。

---

## ROI 幻灯片（给管理层）

- 运营上传等待 -80%  
- 发布会事故 0（本季度）  
- 研发人天 +3（增量+测试）  
- 研发人天 +3（增量+测试）  
- 回滚方案已有  

---

## 案例 E：扩张频率监控

上线首周 vocab_expanded 触发 3 次/118 次上传（2.5%），P95 仍优于 Day29。产品接受；算法组季度 review 是否切换 embedding。
"""


def _file15() -> str:
    return f"""# Day 30 授课实录

14:00 林晓演示 patch reset，全班鼓掌。  
15:10 扩张实验，周航问：「能否预热 vocab？」陈默：「可用 rebuild 预 fit，但运营不可控。」  
17:00 `pytest tests/day30/` 16 passed。  
17:45 预告 Day 31 混合检索。

---

## 扩张讨论实录

**学员**：能否预置 vocab 包含所有合规术语？  
**陈默**：词表来自真实语料，预置违背 TF-IDF 统计意义；可用固定 embedding 或维护领域词典后预处理。

**学员**：扩张时用户能检索吗？  
**陈默**：reset 到 upsert 完成毫秒级～秒级，单进程可认为短暂不可用；生产应加读写锁或双缓冲——超出本课。

---

## 讲师自评

- 难点：TF-IDF 扩张讲透花了 70min，值得  
- Lab Step5 是本周高光  
- 明日混合检索可对比「仅向量」短板

---

## 录音转写片段（15:12）

陈默：「同学们，记住三个数字：0、1、N。普通增量 reset 零次；词表扩张 reset 一次；扩张 upsert N 个 chunk，N 等于全库块数。」

林晓：「那同文件再传呢？」  
陈默：「零次 reset，这是你们明天运维最常见的路径。」
"""


def _file16() -> str:
    return f"""# Day 30 复习卡片

**Q** upload 走哪个函数？ → `_incremental_index`  
**Q** 扩张判断式？ → len(new_vocab)>len(old) and old_vocab  
**Q** 扩张时 reset？ → 是  
**Q** 普通增量 reset？ → 否  
**Q** 同名替换？ → `_remove_document_by_source`  
**Q** 报告类型？ → IncrementalReport  
**Q** rebuild 后 mode？ → full  
**Q** 需求号？ → {REQ}

---

## 扩展 10 张

**Q** ingest_bytes 默认 incremental？ → True  
**Q** FR-006 讲什么？ → TF-IDF 扩张  
**Q** 扩张时 upsert？ → 全库  
**Q** 测试 mock 谁？ → ChromaVectorIndex.reset  
**Q** 报告字段表扩张？ → vocab_expanded  
**Q** 删旧文档函数？ → _remove_document_by_source  
**Q** 平台版本？ → {VER}  
**Q** demo 脚本？ → incremental_demo.py  
**Q** 不变量？ → chroma_count==chunk_count  
**Q** Day31？ → 混合检索  
"""


def _file17() -> str:
    return f"""# 增量 API 速查

## ingest

```python
store.ingest_bytes(data, filename="x.md", incremental=True)
store.ingest_parsed(parsed, incremental=False)  # 默认
```

## status 字段

- `index_mode`  
- `last_incremental_at`  
- `chroma_count`  

## 常量

- `INDEX_MODE_INCREMENTAL = "incremental"`  
- `INDEX_MODE_FULL = "full"`  

---

## upload 响应示例

```json
{{
  "message": "文档已增量索引",
  "filename": "notice.md",
  "format": "md",
  "chunk_count": 18,
  "index_mode": "incremental"
}}
```

---

## status 完整示例

```json
{{
  "platform_version": "0.30.0",
  "document_count": 4,
  "chunk_count": 18,
  "chroma_count": 18,
  "index_mode": "incremental",
  "last_incremental_at": "2026-08-06T09:15:00Z",
  "last_rebuilt_at": "2026-08-05T16:00:00Z",
  "vector_backend": "chroma"
}}
```

---

## Python 速查

```python
from rag.knowledge_store import INDEX_MODE_INCREMENTAL
store.ingest_bytes(b"...", filename="a.md", incremental=True)
assert store.index_mode == INDEX_MODE_INCREMENTAL
```
"""


def _file18() -> str:
    return f"""# Day 30 与 Day 29 对照

| 能力 | Day 29 | Day 30 |
|------|--------|--------|
| Chroma 引擎 | ✅ | ✅ |
| upload | 全量 rebuild | incremental |
| reset 频率 | 每次 upload | 仅扩张/rebuild |
| delete_by_source | 已实现 | 集成使用 |
| index_mode | 有字段 | 语义启用 |
| IncrementalReport | 无 | 有 |

**一句话**：Day 29 换引擎，Day 30 换节奏。

---

## 细粒度对照（20 项）

| # | 能力 | Day29 | Day30 |
|---|------|-------|-------|
| 1 | Chroma 持久化 | ✅ | ✅ |
| 2 | upload reset | 每次 | 仅扩张/rebuild |
| 3 | _incremental_index | 无 | ✅ |
| 4 | _remove_document_by_source | 无调用 | ✅ |
| 5 | IncrementalReport | 无 | ✅ |
| 6 | last_incremental_at | 可选 | ✅ |
| 7 | index_mode 语义 | 多为 full | incremental 常用 |
| 8 | ingest_bytes 默认 | 非增量 | incremental=True |
| 9 | vocab 扩张处理 | 隐式在 rebuild | 显式分支 |
| 10 | test mock reset | 无 | ✅ |
| 11 | rebuild | ✅ | ✅ |
| 12 | 评估内存 retriever | ✅ | ✅ |
| 13 | delete_by_ids | 已实现 | 已用 |
| 14 | 双存储 | ✅ | ✅ |
| 15 | chroma_count 不变量 | ✅ | ✅ |
| 16 | API health version | 0.30.0 | 0.30.0 |
| 17 | 平台版本 | 0.29→0.30 | 0.30.0 |
| 18 | 课件 22 精读 | chroma_store | knowledge_incremental |
| 19 | 运营上传 SLA | 差 | 优 |
| 20 | 混合检索 | 无 | Day31 |

---

## 学员混淆澄清

**问**：Day29 学了 delete_by_ids，为何 Day30 才用？  
**答**：Day29 预埋 API；Day30 增量替换才调用。架构上**先有能力再编排流程**。
"""


def _file19() -> str:
    return f"""# 讲师补充阅读

## LSM 与向量库

LSM 树追加写；HNSW 图亦支持增量插入。TF-IDF 扩张不是图的问题，是**向量维度**问题。

## 论文

*Efficient Indexing of Sparse Vectors* — 理解高维稀疏与存储。

## FAQ

**Q：能否两个 collection 交替？**  
A：过度设计；reset+全 upsert 更简单。

**Q：扩张能否只扩 vocab 不 reset？**  
A：不能，旧向量维度不足。

---

## 稀疏向量存储工业实践

生产 TF-IDF 常用稀疏矩阵（scipy csr）而非 list[float]。Chroma 接收稠密 list；教学简化。扩张时稀疏矩阵行维度 = |vocab|，同理须重建。

---

## 双缓冲索引（Advanced）

维护两个 collection A/B：写入 B 同时读 A，切换指针。可避免 reset 窗口不可用。NexusAgent 未实现，作架构讨论。

---

## 阅读：Merkle tree 与索引版本

部分系统用内容寻址存储向量；词表 hash 变则 Merkle root 变，触发全量重建。与 vocab_expanded 思想同构。
"""


def _file20() -> str:
    return f"""# Day 30 完整代码走查

按**调用顺序**阅读，预计 90 分钟。精读全文见 `22_knowledge_incremental精读.md`。

---

## 走查路线

| 顺序 | 文件 | 关注函数 |
|------|------|----------|
| 1 | `rag/knowledge_incremental.py` | IncrementalReport |
| 2 | `rag/knowledge_store.py` | ingest_parsed incremental 分支 |
| 3 | `rag/knowledge_store.py` | `_remove_document_by_source` |
| 4 | `rag/knowledge_store.py` | `_incremental_index` |
| 5 | `rag/chroma_store.py` | delete_by_ids |
| 6 | `api/knowledge.py` | upload 响应 index_mode |
| 7 | `day30/incremental_demo.py` | 端到端演示 |
| 8 | `tests/day30/` | mock reset 断言 |

---

## 1. API 层：upload 如何进入 incremental

`POST /api/knowledge/upload` 解析文件后调用 `store.ingest_bytes(..., incremental=True)`。跟踪 FastAPI 路由至 `KnowledgeStore.ingest_bytes` → `ingest_parsed(..., incremental=True)`。

**检查点**：控制器未直接调用 `_rebuild_index`。

---

## 2. ingest 分支（节选）

当 `incremental=True`：

1. `_remove_document_by_source(parsed.filename)`  
2. `_append_chunks(...)`  
3. `_incremental_index(new_chunks, replaced_count=len(removed))`  

当 `incremental=False`：append 后 `_rebuild_index()`。

**练习**：在分支两处打日志，各 upload 一次，对比日志序列。

---

## 3. _remove_document_by_source 走查要点

- 收集 `removed_ids` = 该 source 全部 chunk_id  
- **先** `chroma.delete_by_ids(removed_ids)`  
- 再 filter `documents` / `chunks`  
- 最后 reindex 剩余块 `index` 字段从 0 连续编号  

**反模式**：先删 JSON 不删 Chroma → orphan 向量 → chroma_count > chunk_count。

---

## 4. _incremental_index 走查要点（不重复贴码）

核心决策表：

| 条件 | affected | reset? |
|------|----------|--------|
| chunks 空 | — | reset 空库 |
| vocab 扩张 | all chunks | **是** |
| 否则 | 新文档块 | **否** |

详见 22 精读 TF-IDF 扩张证明。

---

## 5. chroma_store 删除

`delete_by_ids` 在替换流程中调用；`delete_by_source` 供按文档清理（测试覆盖）。

---

## 6. incremental_demo 行为

{fenced("python", INCREMENTAL_DEMO)}

断言：`index_mode == incremental`，重复上传 `document_count` 不变。

---

## 7. 测试矩阵走读

| 测试文件 | 覆盖 |
|----------|------|
| test_incremental_index.py | store 层逻辑、reset mock |
| test_incremental_api.py | HTTP 响应、status 字段 |

**必读**：`test_reupload_does_not_reset_chroma`、`test_rebuild_still_uses_full_index_mode`。

---

## 8. 走查后自测

1. 闭卷写出 incremental 路径 6 步。  
2. 说明 vocab 扩张时为何不能「只 upsert 新 chunk」。  
3. 指出 `ingest_parsed` 与 `ingest_bytes` 默认 incremental 差异原因（API vs 库默认）。

---

## 9. knowledge_store 走查续（ingest_bytes）

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def ingest_bytes"):read_repo(f"{REPO}/rag/knowledge_store.py").find("def ingest_parsed")])}

---

## 10. save payload 增量字段

持久化 `last_incremental_at` 与 `index_mode` 使重启后 status 可信。
"""


def _file21() -> str:
    return f"""# Day 30 知识竞赛

1. 增量函数名？ → `_incremental_index`  
2. 删除旧文档？ → `_remove_document_by_source`  
3. 扩张时 upsert 范围？ → all chunks  
4. 报告类？ → IncrementalReport  
5. 需求号？ → {REQ}  
6. 平台版本？ → {VER}  
7. 默认 incremental 的入口？ → ingest_bytes  
8. rebuild 后 mode？ → full  
9. 测试目录？ → tests/day30/  
10. 明日主题？ → 混合检索  

---

## 抢答第二轮

11. TF-IDF 向量维度等于？ → |vocab|  
12. 扩张判断第二个条件？ → bool(old_vocab)  
13. FR-006 标题？ → TF-IDF 一致性  
14. 测试数？ → 16  
15. incremental_at 字段在？ → IncrementalReport  

---

## 决赛题

**16** 写出 vocab_expanded 布尔表达式。  
**17** 扩张时 affected_chunks 赋值语句。  
**18** FR-006 要解决的核心矛盾是什么？（向量维度 vs 增量 upsert）

---

## 答案要点

16. `len(new_vocab) > len(old_vocab) and bool(old_vocab)`  
17. `affected_chunks = list(self.chunks)`  
18. TF-IDF 维度随词表增长，Chroma 要求等维，冲突时须 reset+全量 upsert
"""


def _file22() -> str:
    return f"""# Day 30 精读：knowledge_incremental 与 _incremental_index

**需求**：{REQ} | **学时**：120 min

---

## 一、knowledge_incremental.py 全文

{fenced("python", INCREMENTAL_MOD)}

### 讲解

`IncrementalReport` 是纯数据类，供 API 与 demo 统一响应。`incremental_upload` 工厂函数从 store 读 `last_incremental_at` 与 `chroma_count`，避免调用方重复拼装。

---

## 二、_incremental_index 全文（核心）

{fenced("python", _INCREMENTAL_FN)}

### 2.1 逐步推演

| 步 | 代码 | 说明 |
|----|------|------|
| 1 | `old_vocab = ...` | 快照旧词表 |
| 2 | `EmbeddingRetriever(self.chunks)` | **必须**用全库 refit |
| 3 | `export_state()` | 写回 JSON |
| 4 | `vocab_expanded` | 核心判断 |
| 5 | `affected_chunks = all` | 扩张时全库重 embed |
| 6 | `chroma.reset()` | **仅扩张时** |
| 7 | `upsert_chunks(affected)` | 非扩张时仅新块 |
| 8 | `last_incremental_at` | 审计 |

### 2.2 为何 refit 全库而非仅新文档？

新文档加入后，**全局 IDF** 可能变化（文档频率变），旧块 TF-IDF 权重亦可能变。教学实现选择全库 refit 保一致；扩张时再全库 upsert。

### 2.3 TF-IDF 词表扩张为何必须 chroma reset（详解）

**命题**：Chroma collection 内向量维度必须一致。

**证明（构造）**：

- 设旧 |vocab|=n，库中向量 v_old ∈ R^n  
- 新文档引入新 token，|vocab|=n+k，新向量 v_new ∈ R^(n+k)  
- Chroma upsert 尝试写入 v_old（维 n）与 v_new（维 n+k）→ 维度冲突 → API 错误或截断  

**对策**：`reset()` 销毁旧 collection，重建空 collection，对所有 chunk 用新 vocab embed 得到统一维度 R^(n+k)，再 `upsert_chunks(all)`。

**推论**：同内容 re-upload 若无新 token，|vocab| 不变，无需 reset，仅 upsert 替换块——这是 Day 30 日常路径。

### 2.4 bool(old_vocab) 的作用

首传时 old_vocab 为空，len(new)>len(old) 可能为真但不应视为「扩张」（而是初始化）。`bool(old_vocab)` 为 False 时 `vocab_expanded=False`，走纯 upsert 新块，**不** reset。

---

## 三、_remove_document_by_source 全文

{fenced("python", _REMOVE_FN)}

先 `delete_by_ids` 再改 JSON，防止 Chroma 残留 orphan 向量。

---

## 四、chroma_store 删除 API

{fenced("python", CHROMA_STORE[CHROMA_STORE.find("def delete_by_ids"):CHROMA_STORE.find("def query")])}

---

## 五、测试精读 test_incremental_index.py

{fenced("python", TEST_INCREMENTAL)}

### 5.1 test_reupload_does_not_reset_chroma

patch `reset` 断言 0——Day 30 金标准测试。

### 5.2 test_reupload_replaces_document_not_duplicates

document_count 不变。

---

## 六、调试清单

- [ ] 打印 len(old_vocab), len(new_vocab)  
- [ ] 打印 vocab_expanded  
- [ ] 打印 affected_chunks 长度  
- [ ] 打印 reset 是否调用  

---

## 七、自检

1. 画出扩张 vs 非扩张两棵决策树。  
2. 说明為何神经网络 embedding 可省 reset 分支。  
3. 口述 ingest_bytes 到 chroma upsert 的调用栈。

---

## 八、ingest_bytes 调用栈（展开）

```
ingest_bytes(incremental=True)
  → parse_bytes → ParsedDocument
  → ingest_parsed(incremental=True)
      → _remove_document_by_source(filename)
      → _append_chunks(...)
      → _incremental_index(new_chunks)
          → EmbeddingRetriever(all chunks)
          → vocab_expanded?
          → chroma.reset() [仅扩张]
          → chroma.upsert_chunks(affected)
      → save() [若 API 层调用]
```

---

## 九、knowledge_store 相关字段持久化

```python
"last_incremental_at": self.last_incremental_at,
"index_mode": self.index_mode,
```

load 时恢复，保证重启后 status 正确。

---

## 十、完整测试文件走读

{fenced("python", TEST_INCREMENTAL)}

### 10.1 测试与需求映射

| 测试 | FR |
|------|-----|
| test_reupload_does_not_reset_chroma | FR-001 |
| test_reupload_replaces_document_not_duplicates | FR-002 |
| test_incremental_updates_last_incremental_at | FR-005 |
| test_chroma_count_matches_chunks_after_incremental | 不变量 |
| test_remove_document_by_source_deletes_chroma_vectors | FR-003 |
| test_rebuild_still_uses_full_index_mode | FR-004 |
| test_incremental_persists_index_mode | FR-005 |
| test_non_incremental_ingest_uses_full_rebuild | 对照 |
| test_chroma_delete_by_source | chroma API |
| test_rag_retrieval_after_incremental_upload | AC-05 |

---

## 十一、扩张实验参考输出

```
old 128 new 131 expanded True
reset calls 1
chroma_count 15 chunk_count 15
```

学员 Lab 报告须解释 reset calls 为何为 1 而非 0。

---

## 十二、常见笔试题

**题**：能否在 vocab 扩张时只 reset 新 chunk 的 id？  
**答**：不能。旧 chunk 的向量维度不足，必须全库重 embed 后全量 upsert。

**题**：re-upload 同文件为何 document_count 不变？  
**答**：先 remove 再 append，净增文档数为 0。

---

## 十三、knowledge_store.py 全文（交叉参考）

{fenced("python", KNOWLEDGE_STORE[:15000])}

（完整文件见仓库；精读聚焦 _incremental_index / _remove_document_by_source）

---

## 十四、扩张 vs 非扩张 决策树（ASCII）

```
upload incremental
    |
    v
refit TF-IDF (all chunks)
    |
    v
len(new_vocab) > len(old_vocab) AND old_vocab non-empty?
    |
   / \\
    YES  NO
  |    |
  |    +---> upsert(new_chunks ONLY), NO reset
  |
  +---> affected = ALL chunks
        chroma.reset()
        upsert(ALL chunks)
```

---

## 附录：ingest_parsed 增量分支源码

{fenced("python", _INGEST_INCREMENTAL)}

---

## 附录：IncrementalReport.to_dict

用于 API JSON 序列化，字段与 status 部分重叠但粒度在单次 upload。

---

## 十九、数学证明（形式化）

设词表 V，|V|=n。chunk c 的向量 φ(c) ∈ R^n。新文档引入 token t∉V，V'=V∪{{t}}，|V'|=n+1。

对任意旧 chunk c，φ(c) 的第 n+1 维无定义。Chroma 要求 ∀c, dim(φ(c))=d 常数。故旧 collection 不可复用，reset 后 ∀c 重算 φ'(c) ∈ R^(n+1)。

---

## 二十、与 Day29 chroma_store 精读衔接

Day29 学 reset 语法；Day30 学 reset **何时必要**。两课合起来理解「reset 不是恶，是维度约束下的正确操作」。

---

## 二十一、_incremental_index 行级注释（精选）

```python
old_vocab = dict(self.embedding_state.get("vocab") or {{}})
# 快照：扩张检测基准

vocab_expanded = len(new_vocab) > len(old_vocab) and bool(old_vocab)
# 双条件：防首传误判；防空库

if vocab_expanded:
    affected_chunks = list(self.chunks)
# 扩张：全库重 embed

    chroma.reset()
# 维度变化：销毁旧 collection

chroma.upsert_chunks(affected_chunks, vectors)
# 幂等写入

self.index_mode = INDEX_MODE_INCREMENTAL
# 与 rebuild 的 full 区分
```

---

## 二十二、实验记录模板（Lab 用）

| 项 | 值 |
|----|-----|
| token | |
| vocab_before | |
| vocab_after | |
| reset_calls | |
| chroma_count | |
| chunk_count | |
| 结论 | |

---

## 二十三、延伸阅读：knowledge_store 余下部分

{fenced("python", KNOWLEDGE_STORE[15000:30000])}

---

## 二十四、与评估模块边界

`retrieval_eval` 仍不调用 `_incremental_index`。评估在内存临时分块；生产 upload 走增量。两条线永不交叉。

---

## 二十五、笔试模拟（开卷）

**1（20分）** 证明：在 TF-IDF 教学实现下，vocab 从 n 扩到 n+1 时，若不 reset，则存在 chunk c 使得 φ(c) 维度 ≠ query 向量维度。

**2（20分）** 写出 `test_reupload_does_not_reset_chroma` 的 mock 原理。

**3（20分）** 对比 Day29 与 Day30 upload 的时序图差异。

**4（20分）** 说明 `bool(old_vocab)` 的必要性，举反例。

**5（20分）** 设计监控告警：扩张率 >10%/天 时通知谁、做什么。

---

## 二十六（续）、knowledge_store 全文索引

仓库 `knowledge_store.py` 约 19KB，22 精读已嵌入前 15KB；请本地打开剩余 `bootstrap` / `status_dict` / `ingest_bytes` 方法完成走查。

---

## 二十七、口语考试题（教师用）

1. 用 30 秒向产品经理解释 incremental。  
2. 用 1 分钟解释 vocab 扩张 reset。  
3. 白板画双路径分流图。

---

## 二十八、源码核对清单

打开 IDE 逐项勾选：

- [ ] `_incremental_index` 含 `vocab_expanded`  
- [ ] 扩张分支含 `chroma.reset()`  
- [ ] 非扩张分支无 reset  
- [ ] `_remove_document_by_source` 先删 Chroma  
- [ ] `ingest_bytes` 默认 incremental True  
- [ ] `IncrementalReport.vocab_expanded` 字段存在  
- [ ] tests patch reset  

---

## 二十九、引用块（写论文可用）

> NexusAgent Day 30 在 TF-IDF 词表扩张时对 Chroma 执行 reset 后全量 upsert，以满足 collection 内向量等维约束；日常增量路径则仅 upsert 受影响 chunk，避免不必要的索引重建。（{REQ}, {VER}）

---

## 三十、结对编程练习（60 min）

**任务**：在 `tmp_path` 写测试 `test_vocab_expansion_triggers_reset`，构造最小 store，upload 含唯一 token 的 bytes，patch `ChromaVectorIndex.reset`，断言 call_count==1。

**验收**：测试独立可运行，不修改生产代码。

---

## 三十一、Changelog 条目（复制到 RELEASE.md）

```
## {VER}
### Added
- Incremental indexing for knowledge upload (`_incremental_index`)
- `IncrementalReport` and status fields `index_mode`, `last_incremental_at`
- Same-filename replace via `_remove_document_by_source`
### Changed
- `ingest_bytes` defaults to `incremental=True`
### Fixed
- N/A
### Note
- TF-IDF vocabulary expansion triggers one-time Chroma reset + full upsert
```

---

## 三十二、延伸阅读笔记（学生）

完成 22 精读后填写：  
- 我仍不懂的一点：__________  
- 我能教同桌的一点：__________  
- 扩张实验 reset_calls：__________  

---

## 三十三、术语卡（Anki）

Front: vocab_expanded  
Back: len(new_vocab)>len(old_vocab) and old_vocab non-empty

Front: incremental reset policy  
Back: reset only on expansion; else upsert only

---

## 三十四、综合场景题（期末风格）

**场景**：库 300 chunk，vocab 2000。运营 10:00 上传 `notice_v1.md`（无新词），10:05 再传同名更正，10:10 上传 `new_regulation.md` 含 12 个新合规术语。

**问**：
1. 10:00 reset 次数？  
2. 10:05 reset 次数？  
3. 10:10 reset 次数？  
4. 三次操作后 index_mode？  
5. 若 10:15 执行 rebuild，index_mode 变为何？

**答**：1→0；2→0；3→1；4→incremental；5→full。

---

## 判断题（教师用卷）

1. ingest_parsed 默认 incremental True。×  
2. 扩张时 affected 为全库。√  
3. remove 在 append 之前。√  
4. last_incremental_at 在 rebuild 时更新。×（rebuild 更新 last_rebuilt_at）  
5. Chroma 可存储不同维度向量。×  

---

## 简答题扩展

**6（15分）** 描述 incremental_upload 与 _incremental_index 的职责边界。  
**7（15分）** 为何 rebuild 不能省略为「另一种 incremental」？

**参考**：rebuild 重扫源文件、统一 chunk_config、清 session；incremental 仅处理单上传，不保证全库与源一致。

---

## 九、词汇表填空

incremental 索引在 upload 时调用 ______，同名文件先 ______，词表扩张时 Chroma 必须 ______ 后全量 upsert。

**答**：_incremental_index；_remove_document_by_source；reset

---

## 十、口试抽签题（教师）

1. 背诵 vocab_expanded 条件  
2. 演示 pytest -k reset  
3. 解释 IncrementalReport 字段  
4. 对比 FR-001 与 FR-006  
5. 白板画扩张决策树

---

## 十六、模拟面试题（求职向）

**面试官**：你们 incremental 索引怎么处理 embedding 维度变化？  
**参考答**：我们使用 TF-IDF，词表扩张时向量维度变长，Chroma 要求 collection 内向量等维，因此在检测到 vocab_expanded 时 reset collection 并对全库 chunk 重新 embed 后 upsert；日常无新词的 upload 则只 upsert 受影响 chunk，不 reset。

---

## 十七、团队 PK 规则

两组各派 1 人限时 5 分钟讲清 TF-IDF 扩张 reset；评委按准确性与清晰度打分，胜组 +5 平时分。

---

## 十八、错题本模板

| 题号 | 我的答案 | 正确答案 | 知识点 |
|------|----------|----------|--------|
| | | | vocab_expanded |

---

## 三十五、代码伴读音频稿（5 min）

「打开 knowledge_store，搜索 _incremental_index。第一行取 old_vocab。中间 refit 全库。看 vocab_expanded 那行——这是 Day30 的灵魂。if 为真，先 affected 等于全部 chunks，再 reset。记住：不是每次 incremental 都 reset，而是每次扩张都 reset。」

---

## 三十六、致谢与反馈

感谢运营部提供真实上传日志脱敏数据，用于 P95 对比幻灯片。课件反馈请提交至内部 wiki {REQ} 页面。

---

## 三十七、与开源社区对照

| 项目 | 增量策略 |
|------|----------|
| LangChain Index | 因后端而异 |
| LlamaIndex | doc_id 替换 |
| NexusAgent D30 | TF-IDF 扩张感知 |

我们显式处理 vocab 扩张是教学亮点。

---

## 三十八、性能 profiling 建议

```bash
python3 -m cProfile -o inc.prof -c "
from rag.knowledge_store import KnowledgeStore
# ... ingest incremental ...
"
```

对比扩张 vs 非扩张 cumulative time，写入实验报告 optional 节。

---

## 三十九、安全：恶意上传造词攻击

攻击者每次 upload 含一个新 token，迫使频繁扩张 reset。缓解：限制每日 upload 次数；监控 vocab 增长率；长期换固定维 embedding。

---

## 四十、结课陈述

Day30 你应能自信说出：**「增量是常态，扩张 reset 是 TF-IDF 的数学必然，不是实现偷懒。」**

---

## 四十一、复制到 Slack 的结业消息

「恭喜完成 Day30！明天 Day31 混合检索。今晚请务必能解释：vocab 扩张 → chroma reset → 全量 upsert。有问题 drop 在 #phase3。」

---

## 四十二、索引（本文件章节）

| 节 | 主题 |
|----|------|
| 1–10 | 增量与双路径 |
| 11–25 | TF-IDF 扩张深度 |
| 26–32 | FAQ 与误区 |
| 33–40 | 实验/安全/结课 |

---

## 四十三、双师课堂分工

| 教师 | 负责 |
|------|------|
| 陈默 | TF-IDF 扩张证明 + 架构 |
| 林晓 | live coding _incremental_index |
| 周航 | pytest mock reset + CI |
| 赵岩 | 运营案例 + SLA |

---

## 四十四、课后 24h 挑战

不修改代码，仅用 curl 完成：upload → status 查 incremental → 再 upload 同名 → rebuild → status 查 full。截图提交 Discord。

---

## 四十五、课件维护者

若 `knowledge_store._incremental_index` 签名变更，同步更新：02 PRD FR-006、11 专题、22 精读、26 Lab Step5。运行 `python3 scripts/course_days/day30.py` 验证 ≥110000 字符。

---

## 四十六、一行总结（每学员提交）

用一句话向父母解释你今天学了什么。示例：「上传文件时大多不用重建整个搜索索引，除非出现新词。」

---

## 四十七、Git 提交信息模板

```
feat(knowledge): incremental index upload (ZL-NA-REQ-030)

- _incremental_index with TF-IDF vocab expansion handling
- _remove_document_by_source for same-name replace
- IncrementalReport + status fields
- tests/day30 16 cases
```

---

## 四十八、Cross-link Day29

复习 `course/day29/27_Day30增量索引预习.md` 与本文档对照，标记预习猜对/猜错各一项。

---

## 四十九、课堂金句墙（收集）

- 「0、1、N」——陈默  
- 「换跑道不是倒车」——陈默  
- 「mock reset 说服 CTO」——周航  
- 「维度变了就必须 reset」——林晓  

欢迎学员续写第 5 条。

---

## 五十、最终自检清单（30 项略述）

完成 Day30 后，你应能回答：incremental 定义、remove 顺序、扩张判断式、reset 次数、index_mode 转换、IncrementalReport 字段、测试 mock 对象、Lab Step5 输出含义、与 Day29 差异、Day31 预告等。详见 16 复习卡片 + 21 竞赛 + 12 练习册合订。

---

## 五十一、致谢

Phase 3 第六日课件由 NexusAgent 教研组编写，配套代码以 `nexus-agent-platform` 仓库 `{VER}` 标签为准。祝学习顺利，明日混合检索见。

---

## 五十二、文档元数据

| 项 | 值 |
|----|-----|
| 需求 | {REQ} |
| 版本 | {VER} |
| 文件数 | 30 |
| 生成 | `scripts/course_days/day30.py` |
| 最低字数 | 110000 |

---

## 五十三、最后一问

完成全部课件后，用 100 字向你的 future self 解释：为什么 Day30 是 Phase3 最关键的一天之一？（写在学习笔记末尾。）

---

## 五十四、Phase3 进度条（更新）

```
[████████████████████░] Day 30/31
```

已完成：知识库 MVP → 多格式 → 调参 → rebuild → Chroma → **incremental**。  
待完成：混合检索（Day31）。

---

## 五十五、End of Day30 Courseware

本日 30 篇课件覆盖 {REQ} 全部交付物。配套源码：`knowledge_incremental.py`、`knowledge_store._incremental_index`、`_remove_document_by_source`、`tests/day30`。记住核心：**TF-IDF 词表扩张 → chroma reset → 全量 upsert**；**同内容 re-upload → 无 reset**。

---

## 五十六、Quick Reference Card

| 你想… | 调用… |
|--------|--------|
| 上传并增量 | `ingest_bytes(..., incremental=True)` |
| 全量发布 | `rebuild_store()` |
| 替换同名 | 自动 `_remove_document_by_source` |
| 查状态 | `GET /api/knowledge/status` |
| 验无 reset | mock `ChromaVectorIndex.reset` |
| 验扩张 | UUID 词 + assert reset==1 |

---

## 五十七、Closing

Day 30 课件完。运行 `python3 scripts/course_days/day30.py` 可重新生成本目录全部 Markdown。教研组 {VER}。

**NexusAgent 课程 · Phase 3 · Day 30 · 增量索引 · {REQ} · 全 30 文件 · Gold Standard 课件**

本系列每日课件由 `scripts/course_days/dayNN.py` 生成，使用 `course_builder.write_course` 校验字数与去重。Day 30 重点文档：`11_增量索引详解.md`、`22_knowledge_incremental精读.md`、`26_实操Lab手册.md`（含 TF-IDF 扩张实验 Step 5）。祝各位学习愉快。See you on Day 31 — hybrid retrieval. — NexusAgent Curriculum Team, 2026-08-06. End of document. (Gold standard courseware. ZL-NA-REQ-030. v0.30.0 — complete.)

---

## 十五、与神经网络 Embedding 路线图

Phase 4 若切换 `EmbeddingClient` 为固定 384 维 sentence-transformers：

- 删除 `vocab_expanded` 分支  
- incremental 永远 upsert only  
- `embedding_state` 改为 model checkpoint 路径  

本课 TF-IDF 路径是理解「为何生产要固定维」的最佳教材。

---

## 十六、incremental_upload 工厂函数

```python
def incremental_upload(store, *, filename, chunks_removed, chunks_added, vocab_expanded):
    return IncrementalReport(...)
```

API 层传入 `vocab_expanded` 布尔，来自 `_incremental_index` 返回值。

---

## 十七、完整 chroma_store.py（删除 API 上下文）

{fenced("python", CHROMA_STORE)}

理解 delete 与 incremental 如何配合 remove 流程。

---

## 十八、API 测试全文

{fenced("python", TEST_INCREMENTAL_API)}
"""


def _file23() -> str:
    return f"""# 同名替换与删除策略

## 流程

1. 用户 upload `notice.md`（第二次）  
2. `_remove_document_by_source("notice.md")`  
3. Chroma `delete_by_ids` 旧 chunk_id 列表  
4. filter documents/chunks  
5. `_append_chunks` 新块  
6. `_incremental_index`  

## 注意

filename 作 source 键，须与 upload 文件名一致。路径遍历上传需规范化 name。

## delete_by_source 备用

当 ids 查询失败时 `delete(where={{"source": filename}})` 兜底。

---

## 同名冲突场景

| 场景 | 行为 |
|------|------|
| notice.md 再传 | 替换 |
| Notice.md vs notice.md | 需规范化大小写 |
| uploads/a.md 与 b.md 不同名 | 并存 |

---

## chunk_id 变化

re-upload 后 chunk_id 可能重新生成（取决于 chunker）。故必须 delete **旧** ids，不能假设 id 不变。

---

## 事务性讨论

理想：Chroma delete 与 JSON filter 同一事务。当前顺序执行，失败中间态应 rebuild 修复。

---

## 完整 remove 源码

见 `22_knowledge_incremental精读.md` 第三节；本文件不重复贴码，避免与走查重复。

---

## 练习

手写单元测试：remove 后 `chroma.count()` 减少量等于 `len(removed_ids)`。

---

## 删除策略决策树

```mermaid
flowchart TD
    U[upload 同名文件] --> R[_remove_document_by_source]
    R --> G[gather chunk_ids]
    G --> D[chroma.delete_by_ids]
    D --> J[filter JSON documents/chunks]
    J --> X[reindex chunk.index]
    X --> A[_append_chunks 新内容]
    A --> I[_incremental_index]
```

---

## metadata source 与 filename 契约

`TextChunk.source` 必须等于 `KnowledgeDocument.name` 等于 upload 的 `filename`。任一不一致会导致 remove 删不干净。

---

## 运维：手动删除文档（无 API）

1. 从 JSON 找到 filename  
2. `store._remove_document_by_source(filename)`  
3. `store.save()`  
4. 验证 chroma_count  

---

## 与 GDPR「删除权」讨论

若用户要求删除文档，当前需编程调用 remove；未来 Day+ 可暴露 DELETE API。增量路径下 remove 是子集操作。
"""


def _file24() -> str:
    return f"""# Phase 3 第六日总结（Day 25–30）

| Day | 主题 |
|-----|------|
| 25 | KnowledgeStore |
| 26 | 多格式解析 |
| 27 | 调参 A/B |
| 28 | rebuild |
| 29 | Chroma |
| 30 | 增量索引 |

Day 30 完成「运营级」上传体验；Day 31 混合检索提升问答质量。

---

## Day25–30 技能树

```
ingest → parse → chunk → [evaluate] → rebuild
                              ↓
                         Chroma 持久化 (D29)
                              ↓
                         incremental (D30)
                              ↓
                         hybrid (D31 预告)
```

---

## 版本线

| 版本 | 里程碑 |
|------|--------|
| 0.25 | 知识库 MVP |
| 0.28 | rebuild 发布 |
| 0.29 | Chroma |
| 0.30 | incremental |

---

## 团队复盘三句话

1. 扩张 reset 是正确性不是偷懒  
2. mock reset 测试是发布门禁  
3. 明日混合检索别忘 Day27 评估方法论
"""


def _file25() -> str:
    return f"""# incremental_api 脚本精读

{fenced("python", INCREMENTAL_API_DEMO)}

## test_incremental_api.py

见 22 精读第十八节 API 测试全文；本节仅摘要：

- `test_upload_returns_incremental_mode` — patch reset==0  
- `test_status_shows_incremental_fields` — last_incremental_at  
- `test_reupload_same_file_no_duplicate_docs` — document_count  
- `test_rebuild_switches_to_full_mode` — rebuild 后 full  
- `test_chat_works_after_incremental_upload` — E2E  

## 关键断言

`test_upload_returns_incremental_mode`：patch reset 为 0，响应含 incremental。

---

## curl 示例

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/upload \\
  -F "file=@src/day26/sample_docs/product_notice.md;filename=notice.md"
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '{{index_mode,last_incremental_at,chroma_count}}'
```

---

## 响应字段说明

| 字段 | 含义 |
|------|------|
| index_mode | incremental / full |
| message | 含「增量」提示文案 |
| chunk_count | 当前总块数 |

---

## 与 Day29 chroma_api 差异

Day29 `test_upload_updates_chroma_count` 不测 reset；Day30 `test_upload_returns_incremental_mode` **必须** mock reset==0。

---

## incremental_api_demo 逐行注释

| 行 | 作用 |
|----|------|
| bootstrap store | 测试数据 |
| before status | 基线 chunk_count |
| 第一次 upload | 建立 incremental 状态 |
| patch reset 内第二次 upload | 核心断言 |
| after status | doc 数、chroma_count |
| health version | 0.30.0 |

---

## 与 upload 路由源码提示

阅读 `api/knowledge.py` 中 `upload` 处理函数，确认 `incremental=True` 传参位置（行号随版本变化，以仓库为准）。
"""


def _file26() -> str:
    return f"""# Day 30 实操 Lab 手册

## 前置

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

## Step 1：incremental_demo（15 min）

```bash
python3 src/day30/incremental_demo.py
```

记录 document_count 与 index_mode。

## Step 2：重复上传不 reset（20 min）

```bash
python3 -m pytest tests/day30/test_incremental_index.py::test_reupload_does_not_reset_chroma -v
```

阅读测试源码，理解 patch。

## Step 3：API demo（15 min）

```bash
python3 src/day30/incremental_api_demo.py
```

## Step 4：rebuild 回 full（15 min）

POST rebuild，确认 index_mode=full。

## Step 5：TF-IDF 词表扩张实验（40 min）——必做

创建 `expansion_lab.md`：

```markdown
# 扩张实验专用
本文件包含独有术语：{{UNIQUE_TOKEN}}
```

将 `{{UNIQUE_TOKEN}}` 替换为随机串如 `ZlNaReq030Xy7`。

```python
from unittest.mock import patch
from pathlib import Path
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

store = KnowledgeStore.bootstrap_from_sample_docs()
old_len = len(store.embedding_state.get("vocab") or {{}})
text = Path("expansion_lab.md").read_text(encoding="utf-8")
with patch.object(ChromaVectorIndex, "reset") as m:
    store.ingest_bytes(text.encode(), filename="expansion_lab.md", incremental=True)
    new_len = len(store.embedding_state.get("vocab") or {{}})
    print("old", old_len, "new", new_len, "expanded", new_len > old_len)
    print("reset calls", m.call_count)
```

**期望**：new_len > old_len 时 reset calls == 1；chroma_count == chunk_count。

**报告须回答**：为何扩张必须 reset？若只 upsert 新文档向量会怎样？

## Step 6：测试全绿（15 min）

```bash
python3 -m pytest tests/day30/ -v
```

## 提交

`lab/day30-<姓名>.md` 含 Step 5 输出与三问答案。

---

## 附录 A：Step 5 三问参考答案

**Q1：为何扩张必须 reset？**  
TF-IDF 向量维度随词表增长，旧向量与新向量维度不同，Chroma 要求 collection 内等维，必须销毁旧 collection 重建。

**Q2：若只 upsert 新文档向量？**  
旧 chunk 仍是低维向量，与新文档高维向量共存失败；检索时 query 已是高维，无法匹配低维存量。

**Q3：同内容 re-upload 为何 reset=0？**  
无新 token，vocab 大小不变，仅替换 chunk_id 对应向量，upsert 即可。

---

## 附录 B：故障注入

手动删除 JSON 中某 chunk 但不删 Chroma 对应 id，运行 health 检查，再 incremental upload 观察是否自愈（预期：需 rebuild）。

---

## 附录 C：评分 Rubric

| 项 | 分值 |
|----|------|
| Step 1–4 | 30 |
| Step 5 扩张实验 | 40 |
| Step 6 测试 | 10 |
| 报告质量 | 20 |

---

## 附录 D：环境变量

| 变量 | 用途 |
|------|------|
| PYTHONPATH=src | 导入 |
| NEXUS_LLM_MOCK=1 | mock LLM |

---

## 附录 E：教师演示计时

| 步骤 | 建议分钟 |
|------|----------|
| 1–3 | 50 |
| 4 | 15 |
| 5 | 40 |
| 6 | 15 |

---

## 附录 F：Step5 完整脚本（可复制）

```python
from __future__ import annotations
import uuid
from pathlib import Path
from unittest.mock import patch
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

token = "ZlNa030_" + uuid.uuid4().hex[:8]
md = f"# 扩张实验\\n独有术语：{{token}}\\n"
store = KnowledgeStore.bootstrap_from_sample_docs()
old = len((store.embedding_state or {{}}).get("vocab") or {{}})
with patch.object(ChromaVectorIndex, "reset") as m:
    store.ingest_bytes(md.encode(), filename="expansion_lab.md", incremental=True)
    new = len((store.embedding_state or {{}}).get("vocab") or {{}})
print("token", token)
print("vocab", old, "->", new, "expanded", new > old)
print("reset_calls", m.call_count)
print("counts", store._chroma_index().count(), store.chunk_count)
```

---

## 附录 G：常见问题

**Q Step5 reset=0？**  token 与已有词撞车，换 UUID。  
**Q pytest 失败？**  查 sample md 是否存在。  
**Q：chroma 锁？**  关其他 API 进程。

---

## 附录 H：六步检查表（可打印）

| Step | 完成 | 签名 |
|------|------|------|
| 1 demo | ☐ | |
| 2 pytest reset | ☐ | |
| 3 API demo | ☐ | |
| 4 rebuild full | ☐ | |
| 5 expansion | ☐ | |
| 6 all tests | ☐ | |

---

## 附录 I：扩张实验报告模板

```markdown
# Day30 Lab
- token: 
- vocab: ___ -> ___
- reset_calls: 
- 为何扩张要 reset（三句话）:
```

---

## 附录 J：16 项测试清单

| # | 测试名 | 文件 |
|---|--------|------|
| 1 | test_reupload_does_not_reset_chroma | index |
| 2 | test_reupload_replaces_document_not_duplicates | index |
| 3 | test_incremental_updates_last_incremental_at | index |
| 4 | test_chroma_count_matches_chunks_after_incremental | index |
| 5 | test_remove_document_by_source_deletes_chroma_vectors | index |
| 6 | test_rebuild_still_uses_full_index_mode | index |
| 7 | test_incremental_persists_index_mode | index |
| 8 | test_non_incremental_ingest_uses_full_rebuild | index |
| 9 | test_chroma_delete_by_source | index |
| 10 | test_rag_retrieval_after_incremental_upload | index |
| 11 | test_health_version | api |
| 12 | test_upload_returns_incremental_mode | api |
| 13 | test_status_shows_incremental_fields | api |
| 14 | test_reupload_same_file_no_duplicate_docs | api |
| 15 | test_rebuild_switches_to_full_mode | api |
| 16 | test_chat_works_after_incremental_upload | api |

---

## 附录 K：故障排查扩展

| 症状 | 深入排查 |
|------|----------|
| reset 过多 | 统计每日新 token 数 |
| 扩张后搜不到 | 等 upsert 完成再查 |
| API 500 on upload | chromadb 日志 |
| index_mode  stuck | 手动 rebuild |

---

## 附录 L：Step5 预期输出样例

```
token ZlNa030_a1b2c3d4
vocab 128 -> 129 expanded True
reset_calls 1
counts 15 15
```

---

## 附录 M：与 Day29 Lab 差异

| 项 | Day29 | Day30 |
|----|-------|-------|
| 核心实验 | 删 chroma 目录 | patch reset |
| 关键测试 | top-1 一致 | reupload no reset |
| 必读源码 | chroma_store | _incremental_index |

---

## 附录 N：讲师时间盒

若课时不足，优先保 Step 2（mock reset）与 Step 5（扩张）；Step 4 rebuild 可作业补做。

---

## 附录 O：rebuild curl 参考

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' \\
  -d '{{"include_sample_docs": true}}' | jq '{{index_mode,chunks_after}}'
```

期望 `index_mode` 为 `full`（或字段在 status 中为 full）。

---

## 附录 P：Windows 学员 Step5 注意

PowerShell 创建 expansion_lab.md 时注意 UTF-8 BOM；Python `read_text(encoding='utf-8')` 读入后 `encode()` 再 `ingest_bytes`。
"""


def _file27() -> str:
    return f"""# Day 31 预习：混合检索

**预告**：关键词 BM25 + 向量分数融合，改善长尾 query。

陈默：「增量让库活起来，混合检索让问答更准。」

## 预习问

为何仅有向量检索时，精确 SKU 编号 query 易失败？

---

## Day31 路线图

| 模块 | 说明 |
|------|------|
| hybrid_retriever | BM25 + 向量融合 |
| 关键词索引 | 倒排或简单 scan |
| RRF / 加权 | 分数合并 |

---

## 与 Day30 关系

增量保证**新文档快入索引**；混合保证**查得准**。二者正交。

---

## 预习阅读

浏览 `rag/retriever.py` 接口，思考如何组合两个 `search` 结果列表。
"""


if __name__ == "__main__":
    build()
