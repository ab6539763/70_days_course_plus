#!/usr/bin/env python3
"""Gold-standard course material builder for Day 29 — Chroma 向量库."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_builder import fenced, read_repo, write_course  # noqa: E402

REQ = "ZL-NA-REQ-029"
VER = "v0.29.0"
REPO = "nexus-agent-platform/src"

CHROMA_STORE = read_repo(f"{REPO}/rag/chroma_store.py")
CHROMA_RETRIEVER = read_repo(f"{REPO}/rag/chroma_retriever.py")
KNOWLEDGE_STORE = read_repo(f"{REPO}/rag/knowledge_store.py")
CHROMA_DEMO = read_repo(f"{REPO}/day29/chroma_demo.py")
CHROMA_API_DEMO = read_repo(f"{REPO}/day29/chroma_api_demo.py")
TEST_CHROMA_INDEX = read_repo(f"{REPO}/../tests/day29/test_chroma_index.py")
TEST_CHROMA_API = read_repo(f"{REPO}/../tests/day29/test_chroma_api.py")


def _readme() -> str:
    return f"""# Day 29 课件索引

**日期**：2026-08-05（星期三）  
**主题**：Chroma 向量库持久化  
**需求**：{REQ}  
**平台版本**：{VER}

## 今日交付

| 模块 | 路径 | 说明 |
|------|------|------|
| ChromaVectorIndex | `rag/chroma_store.py` | PersistentClient 封装、upsert/query/reset |
| ChromaEmbeddingRetriever | `rag/chroma_retriever.py` | 与 EmbeddingRetriever 接口对齐 |
| KnowledgeStore 集成 | `rag/knowledge_store.py` | `_rebuild_index` / `_sync_chroma_from_json` |
| status API | `api/schemas.py` | `vector_backend` / `chroma_count` / `chroma_path` |
| 演示脚本 | `src/day29/chroma_demo.py` | 本地验证 Chroma 落盘 |
| 测试 | `tests/day29/` | 15 项（index + API） |

## 关键流程

Day 28 的 `rebuild_store` 流程**不变**；Day 29 将向量从 `store.json` 的 `embedding` 字段**外迁**到 `data/knowledge/chroma/`。JSON 仍保留 TF-IDF 词表（`vocab` / `idf`），供 `EmbeddingClient` 编码 query。

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day29/chroma_demo.py
python3 src/day29/chroma_api_demo.py
python3 -m pytest tests/day29/ -v
```

## 设计决策（课堂必背）

1. **双存储**：`store.json` = 元数据 + TF-IDF 词表；Chroma = chunk 向量 + metadata  
2. **重建语义不变**：`_rebuild_index()` 先 fit TF-IDF，再 `chroma.reset()` + `upsert_chunks`  
3. **冷启动迁移**：`load()` 时若 Chroma 空且 chunks 存在 → `_sync_chroma_from_json()` 自动回填  
4. **评估隔离**：Day 27 `retrieval_eval` 仍用内存 `EmbeddingRetriever`，避免 A/B 实验污染生产 Chroma  

## 课件导航

| 序号 | 文件 | 学时建议 |
|------|------|----------|
| 02 | 需求文档 + 扩展 | 30 min |
| 03 | 架构设计 | 45 min |
| 11 | Chroma 向量库详解 | 60 min |
| 22 | chroma_store 精读 | 90 min |
| 26 | 实操 Lab | 120 min |
| 27 | Day 30 预习 | 15 min |

## 验收命令

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day29/chroma_api_demo.py
PYTHONPATH=src pytest tests/day29/ -q
```

通过标准：`chroma_count == chunk_count`，`vector_backend == "chroma"`，chat 检索正常。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| {VER} | 2026-08-05 | 首版 Chroma 课件 30 篇 |
| 0.28.x | 2026-08-04 | 前一日 rebuild 课件 |

---

## 学员常见问题（课前售后）

**安装 chromadb 失败**：先 `pip install -U pip`，Python 3.10+，ARM 用 conda-forge。  

**data/knowledge 权限**：Docker 挂载卷时注意 uid。  

**Windows 路径**：`chroma_path` 反斜杠由 pathlib 处理，勿手改 JSON。  

**与队友 merge 冲突**：`store.json` 和 `chroma/` 不应进 git；若误提交用 `git rm --cached`。

---

## 学时分配建议（共 6 课时）

| 课时 | 内容 | 文件 |
|------|------|------|
| 1 | PRD + 架构 | 02, 03 |
| 2 | Chroma 专题 | 11 |
| 3 | 源码精读 | 22, 25 |
| 4 | 实操 Lab | 26 |
| 5 | 练习 + 竞赛 | 12, 21 |
| 6 | 作业讲评 + Day30 预习 | 09, 27 |
"""


def _narration() -> str:
    return f"""# Day 29 旁白解读

2026 年 8 月 5 日，星期三。智链科技 NexusAgent 项目组进入 Phase 3 第五日。

林晓打开 `data/knowledge/store.json`，在编辑器里搜索 `"values"`——Day 20 起每个 chunk 的 TF-IDF 向量都嵌在 JSON 里。文件已经 2.3 MB，git diff 一片红。陈默指着监控面板：「词表可以留 JSON，但**向量矩阵**不该再塞进去。今天我们接 Chroma。」

赵岩在白板画了两层：上层 `KnowledgeStore` 管 `documents` / `chunks` / `embedding_state`，下层 `Chroma PersistentClient` 管向量与 ANN 检索。周航问：「`rebuild` 还要跑吗？」陈默点头：「流程不变，`_rebuild_index` 里换成 `chroma.reset()` + `upsert_chunks`。Day 28 的 `rebuild_store` 一行都不用改。」

上午第三节，林晓第一次 `pip install chromadb`。她运行 `chroma_demo.py`，终端打印：

```
向量后端: chroma
Chroma 路径: .../data/knowledge/chroma
块数: 12 / Chroma: 12
```

她故意 `rm -rf data/knowledge/chroma`，重启 API 服务，再调 `GET /api/knowledge/status`——`chroma_count` 仍等于 `chunk_count`。这就是 `KnowledgeStore.load()` 末尾的 `_sync_chroma_from_json()`：从 JSON 元数据重新 embed 并 upsert，**无需人工迁移脚本**。

下午 Lab 第四步，林晓对比内存检索与 Chroma 检索的 top-1 `chunk_id`。`test_chroma_matches_in_memory_retriever_top1` 断言两者一致——换引擎不换分数语义。

```mermaid
journey
    title 林晓的 Day 29
    section 上午
      理解双存储为何必要: 4: 林晓
      走读 ChromaVectorIndex.reset/upsert: 5: 林晓
      对照 Day28 rebuild 调用链: 4: 林晓
    section 下午
      chroma_demo 与 chroma_count 校验: 5: 林晓
      删除 chroma 目录验证冷启动回填: 4: 林晓
      status API 新字段联调: 4: 林晓
```

**今日金句**（陈默）：「JSON 记**是什么**，Chroma 记**像什么**——分工清楚，备份才靠谱。」

**需求编号**：{REQ} | **版本**：{VER}

---

## 技术旁白：store.json 体积变化

林晓用 `wc -c` 对比升级前后：向量外迁后 JSON 从 2.3MB 降至约 180KB。她问：「embedding 字段还剩什么？」陈默打开 JSON：

```json
"embedding": {{
  "vocab": {{ "年化": 0, "收益": 1, "...": "..." }},
  "idf": [ ... ],
  "dimension": 512
}}
```

「没有 `values` 数组了。每个 chunk 的向量只在 Chroma。」

---

## 人物线：周航的 CI 夜

周航凌晨一点 push `test_chroma_api.py`，GitHub Actions 红了：`chromadb` 未缓存。他在 Dockerfile 加 layer，第二天全组 Lab 不用现装依赖。「Day 29 的隐藏交付是 CI 镜像更新。」他在站会开玩笑说。

---

## 与 Phase 3 叙事衔接

Day 25 能存，Day 26 能读多格式，Day 27 能调参，Day 28 能全库发布，Day 29 能**专业存向量**。林晓在日记里写：「离生产又近一步。」
"""


def _prd() -> str:
    return f"""# {REQ} 产品需求文档（PRD）

**需求名称**：Chroma 向量库持久化  
**优先级**：P0  
**状态**：已交付  
**平台版本**：{VER}  
**负责人**：陈默（架构）/ 林晓（实现）/ 周航（测试）

---

## 1. 背景与问题陈述

### 1.1 现状（Day 28 及以前）

- 向量与 TF-IDF 词表均序列化在 `store.json` 的 `embedding` 字段  
- chunk 数量增长后 JSON 体积线性膨胀，全量 load 变慢  
- 无法利用专用向量库的 ANN 索引与运维工具  

### 1.2 目标

将 **chunk 级向量** 迁移至 Chroma `PersistentClient`，JSON 仅保留可复现 TF-IDF 状态的 `vocab` / `idf`（及维度元数据）。检索链路对用户透明：`DocumentIndex` 仍调用 `retriever.search(query, top_k)`。

### 1.3 成功指标

| 指标 | 目标 |
|------|------|
| `chroma_count` | 恒等于 `chunk_count`（非空库） |
| top-1 一致性 | 与内存 `EmbeddingRetriever` 同 query 命中同一 `chunk_id` |
| rebuild 后一致性 | `POST /api/knowledge/rebuild` 后 Chroma 与 JSON 同步 |
| 冷启动 | 删除 chroma 目录后 `load()` 自动回填 |

---

## 2. 功能需求

### FR-001 Chroma 持久化封装

- **文件**：`rag/chroma_store.py`  
- **类**：`ChromaVectorIndex`  
- **持久路径**：`data/knowledge/chroma/`（可通过 `KnowledgeStore.chroma_path` 覆盖）  
- **collection 名**：`nexus_knowledge`  
- **距离度量**：cosine（`metadata={{"hnsw:space": "cosine"}}`）  
- **API**：`reset()` / `upsert_chunks()` / `query()` / `count()` / `delete_by_ids()` / `delete_by_source()`  

### FR-002 ChromaEmbeddingRetriever

- **文件**：`rag/chroma_retriever.py`  
- **接口**：与 `EmbeddingRetriever.search(query, top_k)` 一致，返回 `list[RetrievalResult]`  
- **行为**：`EmbeddingClient.embed(query)` → `chroma.query` → 按 `chunk_id` 关联 `TextChunk`  

### FR-003 KnowledgeStore 集成

- `_rebuild_index()`：  
  1. `EmbeddingRetriever(self.chunks)` 训练 TF-IDF  
  2. `embedding_state = export_state()`  
  3. `chroma.reset()`  
  4. `chroma.upsert_chunks(chunks, vectors)`  
- `_build_rag_service()`：使用 `ChromaEmbeddingRetriever`  
- `_sync_chroma_from_json()`：Chroma 空且 chunks 存在时，从 `embedding_state` 恢复并 upsert  
- `store.json` `version` 升至 **1.1**，新增 `vector_backend: "chroma"`  

### FR-004 HTTP status 扩展

`GET /api/knowledge/status` 响应新增：

- `vector_backend`：字符串，固定 `"chroma"`  
- `chroma_path`：绝对路径字符串  
- `chroma_count`：整数，当前 collection 向量数  

### FR-005 依赖

- `requirements-api.txt` 增加 `chromadb>=0.4`  
- 关闭遥测：`Settings(anonymized_telemetry=False)`  

---

## 3. 非功能需求

### NFR-001 可测试性

- `tests/day29/test_chroma_index.py`：单元级 Chroma + Store  
- `tests/day29/test_chroma_api.py`：FastAPI 集成  

### NFR-002 向后兼容

- 旧版 `store.json`（无 `vector_backend`）load 时默认 `"chroma"` 并触发 `_sync_chroma_from_json`  

### NFR-003 备份策略

运维须**同时备份** `store.json` 与 `chroma/` 目录；仅备份其一可能导致元数据与向量不一致。

---

## 4. 非目标（Out of Scope）

- 替换 TF-IDF 为 OpenAI / 本地神经网络 Embedding API  
- 多 collection 多租户隔离  
- **增量 upsert 单文档**（留给 Day 30 `{REQ.replace('029', '030')}`）  
- 分布式 Chroma Server 部署  

---

## 5. 验收用例（摘要）

| ID | 场景 | 预期 |
|----|------|------|
| AC-01 | bootstrap 后 status | `vector_backend=chroma`, `chroma_count=chunk_count` |
| AC-02 | rebuild | Chroma count 等于 `chunks_after` |
| AC-03 | 删 chroma 后 load | 自动回填，count 恢复 |
| AC-04 | chat | 能检索到「年化收益」相关片段 |
| AC-05 | save JSON | 含 `vector_backend`, `version=1.1` |

---

## 6. 里程碑

- **T+0**：`ChromaVectorIndex` 单元测试绿  
- **T+1**：`KnowledgeStore._rebuild_index` 切换完成  
- **T+2**：API status 字段 + `tests/day29` 全绿  
- **T+3**：课件与 Lab 交付  

---

## 7. 详细用户故事（扩展）

### US-029-A：运维备份

**作为** 运维  
**我希望** 向量数据在独立目录 `data/knowledge/chroma`  
**以便** rsync 时可选择只同步 JSON 或只同步向量  

**验收**：文档 `23_双存储与迁移策略.md` 列出备份命令示例：

```bash
tar czf backup-$(date +%F).tar.gz data/knowledge/store.json data/knowledge/chroma
```

### US-029-B：开发调试

**作为** 开发者  
**我希望** 在 Python REPL 里直接 `ChromaVectorIndex.query`  
**以便** 不启动 API 也能调试向量  

**验收**：`chroma_demo.py` 打印检索预览。

### US-029-C：QA 回归

**作为** QA  
**我希望** 内存与 Chroma top-1 一致  
**以便** 有明确 oracle  

**验收**：`test_chroma_matches_in_memory_retriever_top1` 通过。

---

## 8. API Schema 变更说明

`KnowledgeStatusResponse` 新增字段（Pydantic 模型，示意）：

```python
vector_backend: str = "chroma"
chroma_path: str
chroma_count: int
```

旧客户端忽略未知字段仍可用；新前端知识库页展示「向量引擎：Chroma」徽章。

---

## 9. 发布说明模板（{VER}）

**新增**

- Chroma 持久化向量索引  
- status API：`vector_backend`, `chroma_path`, `chroma_count`  

**变更**

- `store.json` version 1.0 → 1.1  
- 向量不再写入 JSON `embedding` 内联数组  

**迁移**

- 首次启动自动 `_sync_chroma_from_json`  
- 建议全量 `POST /api/knowledge/rebuild` 一次  

**已知限制**

- upload 仍全量 rebuild（Day 30 改进）  

---

## 10. 测试矩阵

| 用例文件 | 数量 | 覆盖 |
|----------|------|------|
| test_chroma_index.py | 10 | 单元+store |
| test_chroma_api.py | 5 | HTTP |
| **合计** | **15** | FR-001~004 |

---

## 11. 开放问题（记录）

1. 是否在 status 暴露 `chroma_collection` 名？（当前固定 nexus_knowledge）  
2. 是否支持 `NEXUS_CHROMA_PATH` 环境变量？（当前用 paths.py）  
3. 多 worker uvicorn 是否共享 PersistentClient？（教学单 worker）

---

## 12. 术语表（PRD 附录）

| 术语 | 英文 | 定义 |
|------|------|------|
| 向量索引 | Vector Index | chunk 嵌入向量的可检索集合 |
| 词表 | Vocabulary | TF-IDF  token → index 映射 |
| 持久化客户端 | PersistentClient | Chroma 本地落盘模式 |
| 双存储 | Dual Storage | JSON 元数据 + Chroma 向量 |
| 冷启动 | Cold Start | 无 chroma 数据时从 JSON 恢复 |
| 全量重建 | Full Rebuild | reset + upsert 全库 |

---

## 13. 跨团队接口

| 团队 | 依赖 Day 29 交付 | 验收方式 |
|------|------------------|----------|
| 前端 | status 新字段展示 | 知识库页显示 Chroma |
| 运维 | 备份 SOP | tar 演练 |
| QA | 15 tests | CI 绿 |
| 产品 | 无感升级 | 同 query 答案一致 |
"""


def _prd_extended() -> str:
    return f"""# {REQ} 需求文档扩展 — 用户故事与验收细节

## Epic：向量引擎外迁

**作为** 运维工程师  
**我希望** 向量数据落盘在专用目录而非巨型 JSON  
**以便** 备份、恢复与容量规划可独立进行  

**作为** 后端开发  
**我希望** `rebuild` 与 `upload` 调用链不因换引擎而大改  
**以便** Day 28 测试与脚本继续有效  

**作为** QA  
**我希望** 内存检索与 Chroma 检索 top-1 一致  
**以便** 回归测试有明确 oracle  

---

## US-029-01：持久化路径可配置

**验收标准**：

1. 默认路径 `get_path("knowledge_chroma")` → `data/knowledge/chroma`  
2. 测试可设 `store.chroma_path = tmp_path / "chroma"`  
3. `status_dict()["chroma_path"]` 返回解析后的绝对路径  

**边界**：路径不存在时 `PersistentClient` 自动 `mkdir`  

---

## US-029-02：upsert 元数据

每个 chunk 写入 Chroma 时 metadata 包含：

| 字段 | 类型 | 用途 |
|------|------|------|
| source | str | 源文件名，供 Day 30 按文档删除 |
| index | int | 块序号 |
| start_char | int | 原文偏移 |
| end_char | int | 原文偏移 |

`documents` 字段存 chunk 正文，便于 Chroma UI 调试（非检索必需）。

---

## US-029-03：cosine 分数对齐

Chroma 返回 `distance`，项目统一 `score = max(0, min(1, 1 - distance))`，与 `EmbeddingRetriever` 教学实现一致。`min_score=0.05` 过滤低分噪声。

---

## US-029-04：评估路径隔离

`rag/retrieval_eval.py` 的 `build_retriever_for_doc` **不得** 实例化 `ChromaVectorIndex`。A/B 实验在内存中完成，避免：

- 测试污染生产 collection  
- CI 并行用例争用同一 persist 目录  

---

## US-029-05：store.json 版本迁移

| 字段 | Day 28 | Day 29 |
|------|--------|--------|
| version | 1.0 | 1.1 |
| vector_backend | 无 | chroma |
| embedding | vocab+idf+（旧版可能含向量） | 仅 vocab+idf 状态 |

load 时若 Chroma 已有数据且 count 匹配，**不**重复 upsert（`_sync_chroma_from_json` 早退）。

---

## 风险登记

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| chromadb 版本 API 变更 | 中 | 中 | pin 版本，CI 锁 requirements |
| 仅删 JSON 丢元数据 | 低 | 高 | 文档强调双备份 |
| TF-IDF 词表与 Chroma 向量不同步 | 中 | 高 | rebuild 全量 reset；Day 30 处理增量 |

---

## 与后续 Day 30 接口预留

Day 29 已在 `ChromaVectorIndex` 实现 `delete_by_ids` / `delete_by_source`，供明日增量替换同名文档时删除旧向量。今日 upload 仍走 `_rebuild_index`（全量），Day 30 才切 `_incremental_index`。

---

## 合规与安全扩展

### 数据驻留

Chroma 数据与 `store.json` 同目录，遵循客户数据不出 VPC 要求。若客户禁止 SQLite 外链，需评估 Chroma Server 私有化部署。

### 审计日志

建议在 `KnowledgeStore._rebuild_index` 与 `_sync_chroma_from_json` 打结构化日志：

```json
{{"event": "chroma_rebuild", "chunk_count": 12, "chroma_count": 12}}
```

便于 SIEM 关联异常检索投诉。

### 权限模型

知识库 API 仍沿用 Day 25 鉴权；Chroma 目录 OS 权限应限制为 API 进程用户只读写，其他用户只读或不可读。
"""


def _architecture() -> str:
    return f"""# Day 29 架构设计 — 双存储与检索链路

**需求**：{REQ} | **版本**：{VER}

## 1. 逻辑架构

```mermaid
flowchart TB
    subgraph API
        UP[POST /upload]
        RB[POST /rebuild]
        ST[GET /status]
        CH[POST /chat]
    end
    subgraph KnowledgeStore
        DOC[documents]
        CHK[chunks]
        EMB[embedding_state TF-IDF]
        RI[_rebuild_index]
        SY[_sync_chroma_from_json]
    end
    subgraph Persistence
        JSON[(store.json)]
        CHR[(chroma/ SQLite+segments)]
    end
    subgraph Retrieval
        EC[EmbeddingClient]
        CER[ChromaEmbeddingRetriever]
        DI[DocumentIndex]
        RAG[RAGContextService]
    end
    UP --> KnowledgeStore
    RB --> RI
    RI --> EMB
    RI --> CHR
    KnowledgeStore --> JSON
    SY --> CHR
    CH --> RAG
    RAG --> CER
    CER --> EC
    CER --> CHR
    ST --> KnowledgeStore
```

## 2. 数据所有权

| 数据 | 权威源 | 副本/索引 |
|------|--------|-----------|
| 文档列表 | JSON `documents` | — |
| 分块文本 | JSON `chunks` | Chroma `documents` 字段（调试） |
| TF-IDF 词表 | JSON `embedding` | EmbeddingClient 内存 |
| 向量 | Chroma `embeddings` | 由 chunks+词表派生，可重建 |

**不变量**：`len(chunks) == chroma.count()`（空库除外）。

## 3. _rebuild_index 时序

```mermaid
sequenceDiagram
    participant KS as KnowledgeStore
    participant ER as EmbeddingRetriever
    participant CV as ChromaVectorIndex
    KS->>ER: new(chunks)
    ER->>KS: embedding_state
    KS->>CV: reset()
    KS->>ER: embed_batch(all texts)
    KS->>CV: upsert_chunks(chunks, vectors)
    Note over KS: index_mode=full (Day30)
```

## 4. 冷启动 load 时序

```mermaid
sequenceDiagram
    participant L as KnowledgeStore.load
    participant J as store.json
    participant CV as Chroma
  L->>J: read documents/chunks/embedding
    L->>CV: count()
    alt count==0 and chunks非空
        L->>CV: upsert_chunks (from embedding_state)
    else count>0
        Note over L: skip sync
    end
    L->>L: _build_rag_service()
```

## 5. 模块依赖

```
knowledge_store.py
  ├── chroma_store.ChromaVectorIndex
  ├── chroma_retriever.ChromaEmbeddingRetriever
  └── embedding_retriever.EmbeddingRetriever  # 仅 rebuild / sync

chroma_retriever.py
  ├── chroma_store.ChromaVectorIndex
  └── embedding.EmbeddingClient

chroma_store.py
  └── chromadb.PersistentClient  # 延迟 import
```

## 6. 配置与路径

`core/paths.py` 中 `knowledge_chroma` 键指向 `data/knowledge/chroma`。测试通过 `store.chroma_path` 注入临时目录，避免污染开发库。

## 7. 与 Day 28 rebuild_store 关系

`rag/knowledge_rebuild.py` 的 `rebuild_store()` 在重扫源文件后调用 `store._rebuild_index()`——**无代码修改**。Day 29 只替换 `_rebuild_index` 内部实现：由「写 JSON 向量」改为「写 Chroma」。

## 8. 安全与运维

- Chroma 目录含 SQLite，热备份建议停写或文件级快照  
- 不在 Chroma metadata 存 PII；正文已在 chunks 中，权限与 JSON 同级  
- 遥测关闭，符合企业内网部署习惯  

---

## 9. 序列图：chat 请求完整路径

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as POST /api/chat
    participant RAG as RAGContextService
    participant DI as DocumentIndex
    participant CER as ChromaEmbeddingRetriever
    participant EC as EmbeddingClient
    participant CV as ChromaVectorIndex
    U->>API: message
    API->>RAG: retrieve_context(message)
    RAG->>DI: retrieve(query)
    DI->>CER: search(query, top_k)
    CER->>EC: embed(query)
    EC-->>CER: query_vector
    CER->>CV: query(query_vector)
    CV-->>CER: ChromaHit[]
    CER-->>DI: RetrievalResult[]
    DI-->>RAG: 拼接上下文
    RAG-->>API: context string
    API-->>U: reply + session_id
```

## 10. 状态机：Chroma collection 生命周期

```mermaid
stateDiagram-v2
    [*] --> Empty: 首次创建
    Empty --> Populated: upsert_chunks
    Populated --> Populated: upsert / query
    Populated --> Empty: reset()
    Empty --> Populated: upsert after reset
    Populated --> Stale: JSON chunks变更未rebuild
    Stale --> Populated: rebuild / sync
```

## 11. 部署拓扑（教学单机）

```
┌──────────────┐
│  uvicorn     │
│  api.app     │
└──────┬───────┘
       │ in-process
       ▼
┌──────────────┐     ┌─────────────┐
│ KnowledgeStore│────▶│ chroma/     │
│ store.json   │     │ (local disk)│
└──────────────┘     └─────────────┘
```

生产多副本时**不能**每副本各写各的 Embedded Chroma；应切 Chroma Server 或共享存储——超出本课范围，记入讲师 FAQ。

## 12. 性能数量级（经验值，非基准承诺）

| chunk 数 | JSON 仅词表 | Chroma query P50 |
|----------|-------------|------------------|
| 50 | load <0.5s | <10ms |
| 500 | load <1s | <20ms |
| 5000 | load ~2s | <50ms |

向量外迁主要收益在 **JSON load 与 git 体积**，非 query 延迟。

## 13. 失败模式与恢复

| 失败模式 | 检测 | 恢复 |
|----------|------|------|
| chroma 目录损坏 | count 异常 / sqlite 错误 | 删 chroma + load sync |
| 词表手改 | top-1 测试失败 | rebuild |
| 仅恢复旧 JSON | vector_backend 缺失 | 自动 bootstrap 逻辑 |
| 磁盘满 | upsert 抛错 | 扩容 + rebuild |

## 14. 架构决策记录 ADR-029

**标题**：采用 Chroma Embedded 作为向量持久化  
**状态**：已接受  
**上下文**：JSON 向量膨胀  
**决策**：双存储，Chroma cosine collection  
**后果**：多 worker 需后续评估；运维双备份  
"""


def build() -> dict[str, str]:
    """Build and write all Day 29 course files. Returns total char count."""
    files: dict[str, str] = {
        "README.md": _readme(),
        "00_旁白解读.md": _narration(),
        "02_需求文档.md": _prd(),
        "02_需求文档_扩展.md": _prd_extended(),
        "03_架构设计.md": _architecture(),
    }
    files.update(_remaining_files())
    return files


def _remaining_files() -> dict[str, str]:
    """Files 04–27 — each with unique pedagogical content."""
    return {
        "01_企业背景与今日任务.md": _file01(),
        "04_流程图与示意图.md": _file04(),
        "05_课堂笔记_上午.md": _file05(),
        "06_课堂笔记_下午.md": _file06(),
        "07_晚自习.md": _file07(),
        "08_作业.md": _file08(),
        "09_作业答案.md": _file09(),
        "10_Chroma验收清单.md": _file10(),
        "11_Chroma向量库详解.md": _file11(),
        "12_课堂练习册.md": _file12(),
        "13_深度扩展_向量库选型.md": _file13(),
        "14_企业案例集_索引迁移日.md": _file14(),
        "15_授课实录.md": _file15(),
        "16_复习卡片.md": _file16(),
        "17_ChromaAPI速查手册.md": _file17(),
        "18_与Day28能力对照表.md": _file18(),
        "19_讲师补充阅读.md": _file19(),
        "20_完整代码走查.md": _file20(),
        "21_课堂知识竞赛.md": _file21(),
        "22_chroma_store精读.md": _file22(),
        "23_双存储与迁移策略.md": _file23(),
        "24_Phase3第五日总结.md": _file24(),
        "25_chroma_api脚本精读.md": _file25(),
        "26_实操Lab手册.md": _file26(),
        "27_Day30增量索引预习.md": _file27(),
    }


# --- Per-file builders (unique content, no shared template) ---

def _file01() -> str:
    return f"""# Day 29 企业背景与今日任务

**智链科技 · NexusAgent 知识库项目组**  
**日期**：2026-08-05 | **需求**：{REQ}

## 晨会纪要

产品部反馈：知识库 JSON 超过 2MB 后，冷启动 API 需要 8 秒。运维希望向量数据能**独立备份**，而不是每次 rsync 整个 `store.json`。CTO 拍板：Phase 3 第五日引入 Chroma 作为向量持久化引擎，版本号升至 **{VER}**。

## 今日任务清单

| 时段 | 任务 | 产出 | 负责人 |
|------|------|------|--------|
| 09:00–10:30 | 研读 PRD FR-001~005 | 疑问列表 | 全员 |
| 10:30–12:00 | 实现 `ChromaVectorIndex` | `chroma_store.py` + 单测 | 林晓 |
| 13:30–15:00 | 集成 `KnowledgeStore._rebuild_index` | 双存储打通 | 林晓 |
| 15:00–16:30 | `ChromaEmbeddingRetriever` + RAG 联调 | chat 检索正常 | 周航 |
| 16:30–18:00 | Lab：`chroma_demo` / 删目录回填实验 | Lab 报告 | 全员 |

## 课前自检

- [ ] 已完成 Day 28 `rebuild_store` Lab  
- [ ] 理解 `EmbeddingRetriever` 与 `embedding_state` 结构  
- [ ] 本地可 `pip install chromadb`  
- [ ] 阅读 `02_需求文档.md` 验收表  

## 今日不做什么

- 不改 upload 的索引策略（仍全量 `_rebuild_index`，Day 30 改增量）  
- 不接入 OpenAI Embedding  
- 不部署远程 Chroma Server  

## 成功标准

下班前 `pytest tests/day29/ -q` 全绿，且能向产品演示：`vector_backend: chroma` 与 `chroma_count` 实时一致。

---

## 企业背景详述

智链科技 B 轮融资后，客服知识库日 upload 从 3 份增至 30 份。Day 28 rebuild 全量尚可接受（12 chunks），但陈默测算：若维持 JSON 内向量，半年后将达 50MB+，Mobile 侧知识库巡检页加载超时。CTO 在 Sprint 计划会点名：「{REQ} 是 Phase 3 硬里程碑，阻塞 Day 30 增量与 Day 31 混合检索。」

竞品「问学堂」已宣传「毫秒级向量检索」。赵岩澄清：「我们教学栈规模小，换 Chroma 主要为**工程化持久化**，不是营销 ANN。」

---

## 今日相关会议

| 时间 | 会议 | 产出 |
|------|------|------|
| 08:30 | 站会 | 确认 chromadb 进 CI 镜像 |
| 09:00 | Day29 kickoff | PRD 走读 |
| 12:00 | 架构评审 | 双存储 ADR 通过 |
| 17:00 | Demo | 产品确认无感升级 |

---

## 阅读作业（课前若未完成）

1. Chroma 官方 Getting Started 前 3 节  
2. 复习 Day 28 `knowledge_rebuild.py` 调用 `_rebuild_index` 的一行  
3. 浏览 `02_需求文档.md` 验收表  
"""


def _file04() -> str:
    return f"""# Day 29 流程图与示意图

## 1. 双存储物理视图

```
data/knowledge/
├── store.json          # documents, chunks, embedding(vocab/idf), vector_backend
├── uploads/            # 运营上传源文件
└── chroma/             # Chroma PersistentClient 数据目录
    ├── chroma.sqlite3
    └── ...             # HNSW 段文件
```

## 2. upsert_chunks 数据流

```mermaid
flowchart LR
    A[TextChunk list] --> B[EmbeddingClient.embed_batch]
    B --> C[EmbeddingVector.values]
    A --> D[ids + metadatas + documents]
    C --> E[collection.upsert]
    D --> E
```

## 3. query 检索数据流

```mermaid
flowchart LR
    Q[用户 query 文本] --> E[EmbeddingClient.embed]
    E --> V[query_vector]
    V --> C[ChromaVectorIndex.query]
    C --> H[ChromaHit chunk_id+score]
    H --> M[_chunks_by_id 映射]
    M --> R[RetrievalResult]
```

## 4. Day 28 → Day 29 变更点（单点）

```mermaid
flowchart TB
    subgraph Day28
        R1[_rebuild_index]
        R1 --> J1[向量写入 JSON embedding]
    end
    subgraph Day29
        R2[_rebuild_index]
        R2 --> J2[词表写入 JSON]
        R2 --> C2[向量写入 Chroma]
    end
```

## 5. 故障恢复决策树

```mermaid
flowchart TD
    S[服务异常] --> Q1{{chroma 目录存在?}}
    Q1 -->|否| A1[load 触发 _sync_chroma_from_json]
    Q1 -->|是| Q2{{chroma_count == chunk_count?}}
    Q2 -->|否| A2[POST rebuild 全量重建]
    Q2 -->|是| Q3{{检索结果异常?}}
    Q3 -->|是| A3[检查 embedding_state 是否被手改]
    Q3 -->|否| A4[查 API 日志]
```

## 6. 课堂白板图（ASCII）

```
┌─────────────────────────────────────────┐
│           KnowledgeStore                 │
│  documents[]  chunks[]  embedding_state │
└───────────────┬─────────────────────────┘
                │ _rebuild_index / sync
                ▼
┌─────────────────────────────────────────┐
│        ChromaVectorIndex                 │
│  collection: nexus_knowledge             │
│  space: cosine                           │
└─────────────────────────────────────────┘
```

---

## 7. rebuild 与 sync 路径对比图

```mermaid
flowchart LR
    subgraph rebuild
        R1[EmbeddingRetriever fit] --> R2[export_state]
        R2 --> R3[chroma.reset]
        R3 --> R4[upsert all]
    end
    subgraph sync
        S1[load JSON] --> S2{{chroma.count==0?}}
        S2 -->|yes| S3[load_state + embed_batch]
        S3 --> S4[upsert all]
        S2 -->|no| S5[skip]
    end
```

rebuild **总是** reset；sync **从不** reset（除非 count 为 0 的等价于空库）。

---

## 8. metadata 在检索后的使用

检索命中 `ChromaHit` 后，`ChromaEmbeddingRetriever` 用 `chunk_id` 回查 `TextChunk`，`_overlap_terms` 生成高亮 token。metadata 中的 `source` 不直接展示给用户，但可用于日志：

```
matched chunk_id=abc source=product_notice.txt index=2 score=0.42
```

---

## 9. 课堂绘图作业

学员手绘「upload Day29 全量 rebuild」时序图，必须包含：parse → append chunks → _rebuild_index → reset → upsert。教师抽查 3 人投影讲解。
"""


def _file05() -> str:
    return f"""# Day 29 课堂笔记（上午）

**讲师**：陈默 | **需求**：{REQ}

## 第一节：为何需要向量库（45 min）

### 痛点回顾

Day 25–28 所有 embedding 向量序列化进 `store.json`。当 chunk 数为 500 时，每向量 512 维 float，JSON 体积约 1MB+，且每次 load 需解析全部浮点数组。

### Chroma 选型理由（教学项目）

| 维度 | Chroma | 纯 JSON |
|------|--------|---------|
| 持久化 | 内置 PersistentClient | 手动 dump |
| 元数据过滤 | `where={{"source": "x"}}` | 自写扫描 |
| 本地部署 | pip install 即可 | — |
| 生产规模 | 中小规模够用 | 不适合 |

### 双存储原则

> JSON 存**可编辑、可 diff 的业务元数据**；Chroma 存**可重建的索引副本**。

词表（vocab/idf）必须在 JSON，因为 query 编码依赖同一套 TF-IDF；向量可从 chunks+词表随时重算。

## 第二节：ChromaVectorIndex API（50 min）

### reset()

删除 collection 再 `get_or_create_collection`。全量 rebuild 必调，保证无残留 id。

### upsert_chunks()

- `ids` = `chunk_id`  
- `embeddings` = TF-IDF 向量 list[float]  
- `metadatas` = source, index, start_char, end_char  

### query()

`n_results = min(top_k, count())`，按 score 降序，过滤 `min_score`。

## 第三节：课堂演示命令

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 -c "
from rag.chroma_store import ChromaVectorIndex
from pathlib import Path
idx = ChromaVectorIndex(Path('/tmp/chroma_test'))
idx.reset()
print('count', idx.count())
"
```

## 第四节：Q&A 摘录

**林晓**：评估实验会写 Chroma 吗？  
**陈默**：不会。`retrieval_eval` 仍用内存 retriever。

**周航**：backup 要拷哪些？  
**陈默**：`store.json` + 整个 `chroma/` 目录。

---

## 第五节：白板推导 — cosine 与 TF-IDF（20 min）

设 query 向量 q，文档向量 d，均已 L2 归一化：

```
cosine_similarity(q, d) = dot(q, d)
cosine_distance = 1 - cosine_similarity  （Chroma 返回）
score = 1 - distance = cosine_similarity
```

因此 `min_score` 过滤的是相似度阈值，而非欧氏距离阈值。若向量未归一化，Chroma cosine 空间与内存点积排序可能分叉——`EmbeddingClient` 实现须保证归一化，这也是 top-1 一致测试存在的原因。

---

## 第六节：chromadb 安装踩坑（15 min）

| 问题 | 解决 |
|------|------|
| `sqlite3` 版本过旧 | 升级 Python 3.11+ |
| ARM Mac 编译失败 | 用预编译 wheel 或 conda |
| 磁盘权限 | `chmod` persist_path |

周航在 CI 镜像预装 `chromadb`，Dockerfile 片段：

```dockerfile
RUN pip install chromadb>=0.4
ENV ANONYMIZED_TELEMETRY=False
```

---

## 第七节：小组练习（15 min）

在 `ChromaVectorIndex.query` 设置 `top_k=1`，对 query「产品风险」打印 `ChromaHit.metadata`，确认 `source` 指向预期 sample 文档。各组派代表在白板写出 `source` 文件名。
"""


def _file06() -> str:
    return f"""# Day 29 课堂笔记（下午）

**讲师**：陈默 + 林晓演示 | **Lab 助教**：周航

## 第四节：KnowledgeStore 集成（60 min）

### _rebuild_index 新实现要点

1. 空 chunks → `embedding_state={{}}` + `chroma.reset()`  
2. 非空 → `EmbeddingRetriever` fit → `export_state()` → `reset()` → `upsert_chunks`  
3. `index_mode = full`（Day 30 字段，今日已写入）  
4. `invalidate_cache()` 清 RAG 单例  

### _sync_chroma_from_json

触发条件：`chunks` 非空、`embedding_state` 非空、`chroma.count()==0`。

步骤：`EmbeddingClient.load_state` → `embed_batch` → `upsert_chunks`（**不** reset）。

### _build_rag_service

```python
client.model.load_state(self.embedding_state)
self._sync_chroma_from_json()  # 兜底
retriever = ChromaEmbeddingRetriever(self.chunks, chroma, client=client)
```

## 第五节：status API（30 min）

新增字段示例：

```json
{{
  "vector_backend": "chroma",
  "chroma_path": "/workspace/nexus-agent-platform/data/knowledge/chroma",
  "chroma_count": 12,
  "chunk_count": 12
}}
```

## 第六节：Lab 实况

林晓执行：

```bash
PYTHONPATH=src python3 src/day29/chroma_demo.py
rm -rf data/knowledge/chroma
PYTHONPATH=src python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.load_or_bootstrap()
print(s.status_dict()['chroma_count'])
"
```

第二次打印仍为 12，验证冷启动回填。

## 故障排查表

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| chroma_count=0 | 未 rebuild / sync 失败 | 手动 `_rebuild_index` |
| top-1 不一致 | 词表与向量不同步 | `POST rebuild` |
| import chromadb 失败 | 未装依赖 | `pip install chromadb` |

---

## 第七节：upload 全量 rebuild 现状（Day 29）

注意：Day 29 **尚未**增量。`ingest_bytes` 默认在 Day 30 才 `incremental=True`；今日 upload 仍触发 `_rebuild_index` → `reset()`。下午有学员误以为 upload 已是增量，陈默澄清：「换引擎不等于换节奏，明天 Day 30。」

验证方式：对 upload 打 patch 监控 `ChromaVectorIndex.reset` 调用次数，Day 29 应为 1，Day 30 重复上传同文件应为 0。

---

## 第八节：代码审查清单（林晓 PR）

- [ ] `chromadb` 延迟 import  
- [ ] `upsert` 元数据四字段齐全  
- [ ] `query` 处理空库  
- [ ] `save` 写入 `vector_backend`  
- [ ] `load` 调用 `_sync_chroma_from_json`  
- [ ] 测试 15 项全绿  
"""


def _file07() -> str:
    return f"""# Day 29 晚自习

**时间**：18:30–20:00 | **形式**：小组讨论 + 可选阅读

## 讨论题

1. 若只备份 `chroma/` 不备份 `store.json`，能否恢复业务？列出缺失的数据。  
2. `cosine` 距离与「TF-IDF 点积后归一化」在教学实现中有何关系？  
3. 为何 Day 27 评估不能写 Chroma？从 CI 并行与数据隔离角度回答。  

## 对比阅读：Milvus vs Chroma vs Qdrant

| 产品 | 部署复杂度 | 适合场景 |
|------|------------|----------|
| Chroma | 低（嵌入式） | 原型、教学、中小规模 |
| Qdrant | 中 | 自托管生产 |
| Milvus | 高 | 大规模分布式 |

**结论**：NexusAgent 教学栈选 Chroma；若客户已有 Qdrant，只需替换 `ChromaVectorIndex` 适配层（接口保持一致）。

## 动手练习（选做）

编写脚本 `scripts/chroma_health.py`：

- 读取 `KnowledgeStore.status_dict()`  
- 若 `chroma_count != chunk_count`，打印 WARNING 并以 exit 1 退出  
- 否则打印 OK  

## 预习 Day 30

阅读 `27_Day30增量索引预习.md`，思考：「upload 时能否不 `reset()`？」写下你的猜想。

---

## 深度讨论：Elasticsearch partial update 对比

晚自习第二题：Elasticsearch 的 partial update 与明日 Chroma incremental upsert 有何异同？

| 维度 | ES partial | Chroma upsert |
|------|------------|---------------|
| 粒度 | 文档/字段 | 向量 id |
| 倒排索引 | 增量更新 posting | HNSW 图增量插入 |
| 词表/映射变更 | 可能 reindex | TF-IDF 扩张需特殊处理 |

**结论预告**：Day 30 在 TF-IDF 词表扩张时会 `chroma.reset()` 后全量 upsert——与 ES mapping 变更触发 reindex 类似。

---

## 晚自习物料：Milvus 10 分钟闪电演讲

每组 3 人，用 1 页 slide 介绍 Milvus 组件（Coordinator、Worker、Segment）。不评分，扩充视野。
"""


def _file08() -> str:
    return f"""# Day 29 作业

**截止**：次日 09:00 | **需求**：{REQ} | **分值**：100 分

## 作业 A：Chroma 健康监控脚本（40 分）

实现 `scripts/chroma_health.py`（或项目组约定路径），要求：

1. 加载 `KnowledgeStore.load_or_bootstrap()`  
2. 比较 `chroma_count` 与 `chunk_count`  
3. 不一致时输出 diff 详情并以非零退出码退出  
4. 支持 `--json` 输出机器可读报告  

**评分**：功能 25 + 错误处理 10 + 代码风格 5  

## 作业 B：源码阅读问答（30 分）

1. `ChromaVectorIndex.reset()` 为何 `delete_collection` 后还要 `_ensure_collection()`？  
2. `_distance_to_score` 为何 clamp 到 [0,1]？  
3. `_sync_chroma_from_json` 在什么条件下**不**执行 upsert？  

## 作业 C：实验报告（30 分）

完成 `26_实操Lab手册.md` 全部六步，提交 Markdown 报告，包含：

- 每步命令与关键输出截图/粘贴  
- 删除 chroma 目录前后 `status` 对比  
- `test_chroma_matches_in_memory_retriever_top1` 的意义一句话总结  

## 提交方式

Git 分支 `homework/day29-<姓名>`，PR 标题 `[Day29] chroma health + lab report`。

---

## 评分细则（教师）

| 等级 | 分数 | 标准 |
|------|------|------|
| A | 90–100 | 脚本健壮 + 报告有深度原理 |
| B | 75–89 | 功能完整，报告略简 |
| C | 60–74 | 脚本有小 bug 但思路对 |
| F | <60 | 未运行或抄袭 |

迟交每天扣 10 分，最多扣 30 分。

---

## 学术诚信

允许讨论思路，禁止粘贴他人 `chroma_health.py` 全文。查重会对 PR diff 做相似度检测。

---

## 扩展挑战（+10 bonus）

实现 `--fix` 标志：当 count 不一致时自动调用 `store._rebuild_index()` 并再次检查。须写清「生产慎用」注释。
"""


def _file09() -> str:
    return f"""# Day 29 作业答案

> 教师版 — 请勿在上课前发给学生

## 作业 A 参考实现

```python
#!/usr/bin/env python3
# Chroma 健康检查 — Day 29 作业参考答案
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "nexus-agent-platform" / "src"
sys.path.insert(0, str(SRC))

from rag.knowledge_store import KnowledgeStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma health check")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    store = KnowledgeStore.load_or_bootstrap()
    status = store.status_dict()
    cc = status.get("chunk_count", 0)
    ch = status.get("chroma_count", 0)
    ok = cc == ch

    report = {{
        "ok": ok,
        "chunk_count": cc,
        "chroma_count": ch,
        "vector_backend": status.get("vector_backend"),
        "chroma_path": status.get("chroma_path"),
    }}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if ok:
            print(f"OK: chroma_count={{ch}} == chunk_count={{cc}}")
        else:
            print(f"WARNING: chroma_count={{ch}} != chunk_count={{cc}}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## 作业 B 答案

1. **reset**：删除后 collection 句柄失效，必须重新 `get_or_create_collection` 才能 upsert。  
2. **clamp**：防止浮点误差导致 UI/API 出现负分或 >1；与产品约定「相似度 0~1」一致。  
3. **不 upsert**：`chroma.count() > 0` 时早退；或 chunks/embedding_state 为空。  

## 作业 C 评分要点

| 项 | 满分 | 要点 |
|----|------|------|
| Lab 六步完整 | 15 | 命令可复现 |
| 删 chroma 实验 | 10 | 前后 count 对比 |
| top-1 测试意义 | 5 | 「换引擎不换排序语义」 |
"""


def _file10() -> str:
    return f"""# Day 29 Chroma 验收清单

**版本**：{VER} | **教师勾选**

## 代码交付

- [ ] `rag/chroma_store.py` 存在且 `VECTOR_BACKEND == "chroma"`  
- [ ] `rag/chroma_retriever.py` 实现 `search()`  
- [ ] `knowledge_store._rebuild_index` 调用 `chroma.reset` + upsert  
- [ ] `knowledge_store._sync_chroma_from_json` 实现冷启动  
- [ ] `requirements-api.txt` 含 chromadb  

## 测试

- [ ] `pytest tests/day29/test_chroma_index.py` 全绿（10 项）  
- [ ] `pytest tests/day29/test_chroma_api.py` 全绿（5 项）  
- [ ] `test_chroma_matches_in_memory_retriever_top1` 通过  

## API

- [ ] `GET /api/knowledge/status` 含 `vector_backend`, `chroma_path`, `chroma_count`  
- [ ] `POST /api/knowledge/rebuild` 后 `chroma_count == chunks_after`  
- [ ] `POST /api/chat` 检索正常  

## 演示脚本

- [ ] `python3 src/day29/chroma_demo.py` 打印 ✅  
- [ ] `python3 src/day29/chroma_api_demo.py` 打印 ✅  

## 课件

- [ ] 30 篇课件齐全  
- [ ] `22_chroma_store精读.md` 含完整源码  
- [ ] 学员 Lab 报告 ≥ 1 份归档  

**验收签字**：___________  **日期**：___________

---

## 验收场景脚本（教师现场）

```bash
set -e
export PYTHONPATH=src NEXUS_LLM_MOCK=1
pytest tests/day29/ -q
python3 src/day29/chroma_demo.py | grep -q "✅"
python3 src/day29/chroma_api_demo.py | grep -q "✅"
echo "DAY29_ACCEPTANCE_OK"
```

---

## 常见验收失败与处置

| 失败项 | 处置 |
|--------|------|
| chroma_count 偏差 | rebuild + 查 JSON chunks |
| import chromadb | pip install -r requirements-api.txt |
| chat 空回复 | 查 embedding_state 是否空 |
| version 不匹配 | 查 PLATFORM_VERSION 常量 |

---

## 学员签字确认

本人已完成 Lab 六步并理解双存储备份要求：___________ 日期 _______
"""


def _file11() -> str:
    return f"""# Chroma 向量库详解（Day 29 专题讲义）

**需求**：{REQ} | **建议学时**：90 分钟

## 1. 向量数据库在 RAG 中的位置

检索增强生成（RAG）链路：`query → embed → ANN search → top-k chunks → LLM`。Day 19–28 用内存列表存向量；Day 29 起向量落盘 Chroma，使 API 进程重启后**无需重算全库 embed**。

## 2. Chroma 核心概念

| 概念 | 说明 |
|------|------|
| Client | `PersistentClient(path=...)` 或 HTTP Client |
| Collection | 命名空间，类似 SQL 表 |
| Document | 可选文本，便于调试 |
| Embedding | float 向量 |
| Metadata | 过滤用键值，如 source |
| ID | 唯一字符串，我们用 chunk_id |

## 3. PersistentClient 落盘机制

Chroma 在 `path` 下创建 SQLite 元数据 + 二进制向量段。重启后 `get_or_create_collection` 恢复同一 collection。

```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="data/knowledge/chroma",
    settings=Settings(anonymized_telemetry=False),
)
col = client.get_or_create_collection(
    name="nexus_knowledge",
    metadata={{"hnsw:space": "cosine"}},
)
```

## 4. cosine 空间

`hnsw:space: cosine` 表示用 cosine 距离。返回的 `distance` 越小越相似。项目统一：

```
score = 1 - distance  （clamp 到 [0,1]）
```

与 `EmbeddingRetriever` 内积+归一化教学实现排序一致。

## 5. upsert 语义

`upsert` = insert or update。同一 `chunk_id` 重复写入会覆盖向量与 metadata，**不会**产生 duplicate id。全量 rebuild 前先 `reset()` 是为清空已删除 chunk 的残留 id。

## 6. metadata 设计权衡

我们存 `source/index/start_char/end_char`，不存全文（全文在 JSON chunks）。好处：metadata 体积小；过滤可按文档删（Day 30）。坏处：Chroma 单独无法重建完整 KnowledgeStore——**必须以 JSON 为权威源**。

## 7. 教学规模 vs 生产规模

本课程 chunk 数 < 100，Chroma 内部 HNSW 与暴力扫描差异不明显。`test_chroma_matches_in_memory_retriever_top1` 保证语义一致。生产上万 chunk 时，ANN 优势才显著。

## 8. 常见错误

| 错误 | 后果 |
|------|------|
| 忘记 reset 就全量 rebuild | 残留已删 chunk 的向量 |
| 词表更新但向量未重算 | top-1 错乱（Day 30 处理增量） |
| 多进程写同一 persist 目录 | SQLite 锁冲突 |

## 9. 与 OpenAI Embedding 路线对比

| 方案 | 优点 | 本项目阶段 |
|------|------|------------|
| TF-IDF + Chroma | 无外部 API、可离线 | ✅ 当前 |
| ada-002 + Chroma | 语义更强 | 后续 Phase |

词表仍在 JSON，换 Embedding 模型只需改 `EmbeddingClient`，`ChromaVectorIndex` 接口不变。

## 10. 课堂演示 checklist

- [ ] `collection.count()` 与 `len(chunks)` 一致  
- [ ] `query` 返回的 metadata.source 正确  
- [ ] 删除 persist 目录后 load 自动恢复  

## 11. Chroma 与 SQLite 事务（深入）

PersistentClient 在 `path` 下维护 `chroma.sqlite3`。每次 `upsert` 或 `delete` 会更新 SQLite 中的 id 索引，向量数据写入伴生段文件。理解这一点有助于解释：

- 为何**多进程同时写**同一 `persist_path` 可能触发 `database is locked`  
- 为何复制 `chroma/` 目录时建议先停写（或接受快照一致性）  
- 为何「只删 sqlite 不删段文件」会导致 collection 损坏  

教学环境单进程 API 不会遇到锁问题；周航在 CI 中为每个 `tmp_path` 分配独立 chroma 目录正是为了避免并行测试争用。

## 12. collection metadata 与距离空间

创建 collection 时传入 `metadata={{"hnsw:space": "cosine"}}`。此后该 collection 内所有向量按 cosine 空间建 HNSW 图。若误用 L2 collection 写入 TF-IDF 向量，排序会与 `EmbeddingRetriever` 不一致，`test_chroma_matches_in_memory_retriever_top1` 会失败。

**课堂实验**：不必真改空间；阅读 Chroma 文档对比 `cosine` 与 `l2` 返回 distance 量纲差异。

## 13. upsert 与 add 的区别

Chroma 提供 `add`（仅插入）与 `upsert`（插入或覆盖）。我们选择 upsert 因为：

1. 全量 rebuild 后 `reset()` 清空 collection，`add` 亦可；但增量路径（Day 30）需覆盖同 `chunk_id`  
2. 幂等重试：网络抖动重放 upsert 不会产生 duplicate id 错误  

## 14. query 参数 n_results 边界

```python
n_results = max(1, min(top_k, collection.count()))
```

当 `top_k=10` 但库中只有 3 条向量时，Chroma 只能返回 3 条。客户端不应假设永远返回 `top_k` 条。`ChromaEmbeddingRetriever` 末尾再 `[:max(1, top_k)]` 做二次截断。

## 15. min_score 过滤语义

`min_score=0.05` 过滤极低相似度 hit，减少 RAG 上下文噪声。TF-IDF 在短 query 上可能出现「有命中但分数低」的情况；过滤后 `search` 返回空列表，`RAGContextService` 应优雅降级（项目已有「未检索到」文案）。

调参建议：评估集上扫 `min_score` ∈ {{0, 0.05, 0.1}}，观察 hit_rate 与噪声率权衡——Day 27 评估脚本可复用。

## 16. delete_by_source 实现细节

Day 29 已实现供 Day 30 使用。逻辑分两步：

1. `collection.get(where={{"source": source}}, include=[])` 取出 ids  
2. `collection.delete(ids=ids)` 或 `delete(where=...)` 兜底  

不同 chromadb 版本 `where` 语法略有差异；项目用 try/except 兼容。生产升级 chromadb 时须跑 `tests/day30/test_chroma_delete_by_source`。

## 17. EmbeddingClient 与 Chroma 的分工

| 步骤 | 组件 | 输入/输出 |
|------|------|-----------|
| 训练词表 | EmbeddingRetriever / fit | chunks → vocab/idf |
| 导出状态 | export_state() | dict → JSON |
| 编码 query | EmbeddingClient.embed | str → EmbeddingVector |
| 编码 batch | embed_batch | list[str] → list[EmbeddingVector] |
| 存储向量 | ChromaVectorIndex | list[float] → 磁盘 |
| ANN 检索 | Chroma query | query_vector → ChromaHit |

Chroma **不负责** TF-IDF 训练；若 JSON 词表与 Chroma 向量来自不同 fit 轮次，检索必错。

## 18. 版本 pin 策略

`requirements-api.txt` 建议写 `chromadb>=0.4,<0.6`（示例）。大版本升级时关注：

- `PersistentClient` 构造函数参数  
- `collection.query` 返回字段名  
- `delete` 是否支持 `where`  

锁定版本后，在 README 注明「升级须全量 regression」。

## 19. 可观测性建议

生产可在 `status` 之外增加：

- `chroma_last_sync_at`（若实现异步 sync）  
- `chroma_disk_bytes`（`du -sb chroma/`）  
- 定时任务跑作业 A `chroma_health.py`  

教学项目以 `chroma_count == chunk_count` 为健康唯一硬指标。

## 20. 术语表

| 术语 | 定义 |
|------|------|
| ANN | 近似最近邻，HNSW 等算法 |
| collection | Chroma 内向量表 |
| chunk_id | 业务主键，贯穿 JSON 与 Chroma |
| embedding_state | TF-IDF vocab/idf 序列化 dict |
| persist_path | Chroma 数据目录 |
| dual storage | JSON 元数据 + Chroma 向量 |
"""


def _file12() -> str:
    return f"""# Day 29 课堂练习册

**姓名**：___________ **得分**：___________

## 一、选择题（每题 4 分，共 40 分）

**1.** Day 29 后 TF-IDF 词表存储在哪里？  
A. 仅 Chroma  B. 仅 store.json  C. 两者都有  D. 内存不落盘  
<details><summary>答案</summary>B — embedding_state 在 JSON</details>

**2.** 全量 rebuild 前对 Chroma 应调用？  
A. upsert  B. query  C. reset  D. delete_by_source  
<details><summary>答案</summary>C</details>

**3.** `_sync_chroma_from_json` 触发条件之一是？  
A. chroma.count()>0  B. chroma.count()==0 且 chunks 非空  C. documents 为空  D. 任意时刻  
<details><summary>答案</summary>B</details>

**4.** `vector_backend` 字段值为？  
A. json  B. faiss  C. chroma  D. pinecone  
<details><summary>答案</summary>C</details>

**5.** Day 27 评估为何不用 Chroma？  
A. Chroma 太慢  B. 避免污染生产索引  C. Chroma 不支持 TF-IDF  D. 未安装  
<details><summary>答案</summary>B</details>

**6.** Chroma 使用的距离度量？  
A. L2  B. cosine  C. dot  D. hamming  
<details><summary>答案</summary>B</details>

**7.** store.json version Day 29 为？  
A. 1.0  B. 1.1  C. 2.0  D. 0.29  
<details><summary>答案</summary>B</details>

**8.** `ChromaEmbeddingRetriever.search` 返回类型？  
A. str  B. ChromaHit  C. RetrievalResult 列表  D. dict  
<details><summary>答案</summary>C</details>

**9.** 备份知识库至少要包含？  
A. 仅 JSON  B. 仅 chroma  C. JSON + chroma  D. uploads  
<details><summary>答案</summary>C</details>

**10.** Day 30 将改进？  
A. 换 FAISS  B. 增量 upsert  C. OCR  D. 删除 JSON  
<details><summary>答案</summary>B</details>

## 二、简答题（每题 10 分，共 30 分）

**11.** 画出双存储架构，标出 documents/chunks/embedding 与 Chroma 各自存什么。

**12.** 解释 `score = 1 - distance` 的含义。

**13.** 描述删除 `chroma/` 目录后重启服务的恢复流程。

## 三、实操题（30 分）

在本地运行 `pytest tests/day29/test_chroma_index.py::test_load_restores_chroma_from_json -v`，粘贴输出并解释该测试证明了什么。

---

## 四、附加选择题（ bonus ）

**14.** `ChromaVectorIndex` 中 `COLLECTION_NAME` 默认值？  
<details><summary>答案</summary>nexus_knowledge</details>

**15.** `_ensure_client` 中关闭遥测的设置？  
<details><summary>答案</summary>Settings(anonymized_telemetry=False)</details>

**16.** `upsert_chunks` 若 chunks 与 vectors 长度不一致？  
<details><summary>答案</summary>raise ValueError</details>

**17.** `ChromaHit` 包含哪些字段？  
<details><summary>答案</summary>chunk_id, score, metadata</details>

**18.** Day 29 平台版本？  
<details><summary>答案</summary>{VER}</details>

---

## 五、代码阅读题（20 分）

阅读 `chroma_store.py` 中 `delete_by_source`，说明为何先 `get` 再 `delete(ids=)`，而不是只 `delete(where=)`。

**参考答**：部分 chromadb 版本对 `delete(where=)` 支持不稳定；先 `get` 拿到 ids 再 `delete(ids=)` 兼容性更好。若 `get` 失败则 fallback `delete(where=)`。

---

## 六、简答题评分 Rubric

| 题号 | 满分要点 |
|------|----------|
| 11 | 两层存储图 + 四类数据归属 |
| 12 | distance 越小越相似，score 是相似度 |
| 13 | load → _sync_chroma_from_json → embed_batch → upsert |

---

## 七、教师用卷面说明

考试时间 45 分钟；允许带一张 A4 手写笔记；不准开 IDE。实操题可课后补交截图。
"""


def _file13() -> str:
    return f"""# 深度扩展：向量库选型（Day 29）

## 1. 选型维度矩阵

| 维度 | Chroma | Qdrant | Milvus | pgvector |
|------|--------|--------|--------|----------|
| 嵌入式部署 | ✅ | Docker | K8s 集群 | PostgreSQL 扩展 |
| 元数据过滤 | ✅ | ✅强 | ✅ | SQL |
| 多租户 | 弱 | ✅ | ✅ | ✅ |
| 运维成熟度 | 中 | 高 | 很高 | 依赖 PG |
| 学习曲线 | 低 | 中 | 高 | 中 |

## 2. 为何教学选 Chroma

NexusAgent 课程强调**最小可运行路径**：`pip install chromadb` 即可，无需 Docker Compose。接口简洁，与 Python dataclass 教学风格一致。

## 3. 迁移到 Qdrant 的适配层思路

保留 `ChromaVectorIndex` 同名方法：`reset/upsert_chunks/query/count/delete_*`。内部换 Qdrant Client。`KnowledgeStore` 零修改——这就是**端口适配器模式**。

## 4. 云向量库（Pinecone / Zilliz Cloud）

优点：免运维、自动扩缩。缺点：数据出境、成本、内网合规。智链 B 轮客户多为金融，倾向私有化 Chroma/Qdrant。

## 5. BM25 + 向量混合

Day 31 将讲混合检索。向量库选型需支持**同一 query 多次检索**或融合层独立。Chroma 单路向量足够教学。

## 6. 案例：某券商知识库 POC

- 10 万 chunk → Qdrant 集群  
- 元数据 `department/regulation_version` 过滤  
- NexusAgent 课程架构与之同构，仅规模不同  

## 7. 阅读清单

- Chroma 官方 docs：Persistent Client  
- Qdrant：Filtering  
- MTEB 排行榜：理解 Embedding 质量差异  

---

## 8. 详细对比：Chroma vs FAISS

| 维度 | Chroma | FAISS |
|------|--------|-------|
| 持久化 | 内置 | 需手动 save index |
| 元数据过滤 | ✅ | 需自研 |
| Python API 友好度 | 高 | 中 |
| 大规模 ANN | 中 | 很高 |
| 教学曲线 | 低 | 中 |

NexusAgent 曾考虑 FAISS Day 24，但 metadata 与持久化样板代码多，最终 Day 29 选 Chroma。

## 9. 云厂商托管向量服务

**Pinecone / Zilliz Cloud / AWS OpenSearch k-NN**

优点：免运维、弹性。缺点：成本随维度与 QPS 上升；金融客户数据出境审批。智链国内客户 POC 用嵌入式 Chroma，合同交付可换 Qdrant on-prem。

## 10. 选型决策树

```mermaid
flowchart TD
    A[需要向量持久化?] -->|否| M[内存 EmbeddingRetriever]
    A -->|是| B{{规模}}
    B -->|<10万 chunk| C[Chroma Embedded]
    B -->|10万~百万| D[Qdrant/Milvus]
    B -->|>百万| E[Milvus 集群]
    C --> F{{要 metadata 过滤?}}
    F -->|是| C
    F -->|否| G[FAISS 可考虑]
```

## 11. 成本粗算（示意）

假设 1 万 chunk，512 维，Chroma 磁盘约 20–40MB；云向量托管月费可能数十美元起。教学项目忽略云成本，企业标书须写清 TCO。

## 12. 学员调研作业（关联本扩展）

任选 Chroma / Qdrant / Milvus 官网，写 200 字「若替换 ChromaVectorIndex 需要改哪些方法」。不提交代码，仅接口列表。
"""


def _file14() -> str:
    return f"""# 企业案例集：索引迁移日（Day 29）

## 案例背景

**客户**：智链科技内部客服知识库  
**时间**：2026-08-05  
**事件**：上线 Chroma 前夜，`store.json` 达 4.7MB，CI 全量测试 load 超时。

## 问题现象

- API 冷启动 12s  
- git 合并 `store.json` 频繁冲突  
- 运维无法单独增量备份向量  

## 迁移方案（陈默设计）

### 阶段 1：并行写入（未采用）

同时写 JSON 向量与 Chroma——回滚简单但双倍写入，否决。

### 阶段 2：切换写入（采用）

Day 29 起 `_rebuild_index` 只写 Chroma；JSON 删向量字段，仅留词表。旧版 JSON load 时 `_sync_chroma_from_json` 首次回填。

### 阶段 3：验证

| 检查项 | 迁移前 | 迁移后 |
|--------|--------|--------|
| store.json 大小 | 4.7MB | 180KB |
| 冷启动 | 12s | 2.1s |
| top-1 命中率 | 基准 | 100% 一致 |

## rollback 预案

保留 Day 28 git tag。若 Chroma 故障，checkout 旧版 + 清空 chroma 目录，回到 JSON 向量模式（仅紧急）。

## 经验教训

1. **双备份**成为运维 SOP 新条目  
2. **test_chroma_matches_in_memory_retriever_top1** 纳入发布门禁  
3. 产品侧感知不到引擎变化——接口稳定的价值  

## 课堂讨论

若客户已购 Qdrant 企业版，NexusAgent 应如何报价定制适配？列出 3 人天还是 10 人天的理由。

---

## 附录：迁移日时间线（逐小时）

| 时间 | 事件 |
|------|------|
| 08:00 | 冻结 main，打 tag v0.28.0 |
| 09:00 | 合并 Day 29 PR，CI 全绿 |
| 10:00 |  staging 删 chroma 测 sync |
| 11:00 | 生产备份 tar |
| 11:30 | 部署 {VER} |
| 12:00 | status 验收 chroma_count |
| 14:00 | 客服抽样 20 条 chat |
| 16:00 | 宣布迁移完成 |

---

## 附录：客户沟通话术（赵岩）

「本次升级对业务透明：检索答案质量不变，后台向量改为专业存储，后续上传会更快（Day 30）。」

避免说「我们换了数据库」引发不必要的合规审查；可说「索引引擎优化」。

---

## 案例 B：金融机构合规检查

合规部问：「向量里是否含客户 PII？」赵岩答复：「向量是 TF-IDF 数值，不可逆推原文；PII 若在上传文档中，JSON chunks 与 Chroma documents 字段均有，权限与源文件一致。」Chroma 不新增合规面，仅改变向量物理存储。

---

## 案例 C：误删 chroma 的值班故事

夜班运维误执行 `rm -rf data/knowledge/chroma`。早班 API 自动 `_sync_chroma_from_json`，服务恢复，仅冷启动多 3 秒 embed。陈默据此将「双存储」写入事故复盘：**元数据权威在 JSON** 救了场。

---

## ROI 估算（示意）

| 项 | 迁移前 | 迁移后 |
|----|--------|--------|
| JSON 备份时间 | 45s | 8s |
| git clone 仓库 | 大 | 小 |
| 检索 P99 | 基准 | 相近 |

向量外迁 ROI 在运维与协作，不在毫秒级延迟。
"""


def _file15() -> str:
    return f"""# Day 29 授课实录（摘要）

**时间**：2026-08-05 09:00–18:00  
**地点**：智链科技 3F 会议室  
**出勤**：林晓、周航、赵岩、实习生 2 人

## 09:05 开场

陈默展示 4.7MB `store.json` diff，提问：「向量应该和词表放在一起吗？」全场否定。引出 {REQ}。

## 10:20 ChromaVectorIndex  live coding

林晓实现 `upsert_chunks`，第一次忘记 `metadatas` 里 `index` 字段，导致 query 排序不稳定。陈默强调 metadata 契约。

## 11:45 双存储架构图

赵岩问：「Chroma 丢了能否只靠 JSON 恢复？」陈默：「能，`_sync_chroma_from_json` 就是干这个的。」

## 14:00 下午 Lab

周航带领删除 chroma 目录实验。实习生误删 `store.json`，从 git 恢复，陈默借机讲**双备份**。

## 16:30 test 全绿

`pytest tests/day29/ -v` 15 passed。团队拍照发 Slack #phase3。

## 17:45 明日预告

「Day 30 upload 不再每次 reset——增量索引。」林晓：「终于像生产了。」

## 讲师自评

- 节奏：正常  
- 难点：cosine distance 解释多花了 15min  
- 改进：提前发 chromadb 安装文档  

---

## 实录附录：关键对话原文

**陈默**：「你们可以把 Chroma 当成 JSON 的**索引副本**。副本坏了，从 JSON 重建；JSON 坏了，有备份。」

**林晓**：「那 evaluation 为啥不用副本？」

**陈默**：「A/B 是实验室，production 是门店。实验室打翻试剂不能污染门店库存。」

**赵岩**：「投资人问我们用什么向量库，我说 Chroma 嵌入式，单机百万级以下够用。他问百万以上呢？我说 Qdrant，接口一样。」

**周航**：「CI 里每个测试独立 tmp chroma，我昨晚跑了 200 次并行，零锁。」

---

## 学员反馈（课后问卷摘要）

| 问题 | 平均分 1–5 |
|------|------------|
| 双存储概念清晰度 | 4.2 |
| Lab 难度 | 3.8 |
| 源码阅读量 | 4.5 |
| 节奏 | 4.0 |

**开放意见摘录**：「希望 Day 30 早点讲增量」「22 精读很有用，代码太长建议课前发」。

---

## 时间轴补充

| 时刻 | 事件 |
|------|------|
| 10:05 | 第一次 upsert 成功掌声 |
| 11:30 | 赵岩讲备份 SOP |
| 14:20 | 林晓删 chroma 演示 |
| 15:45 | test top-1 一致讲解 |
| 17:00 | 产品远程观看 demo |
| 17:50 | 布置作业 A health 脚本 |

---

## 未收录进教材的插曲

实习生把 `collection_name` 改成 `test`，全组 status 报 count 0——教训：常量勿改，用 `chroma_path` 隔离环境。
"""


def _file16() -> str:
    return f"""# Day 29 复习卡片

> 打印裁剪，正面问题背面答案

---

**Q1** Day 29 核心交付的两个 Python 模块？  
**A1** `chroma_store.py` + `chroma_retriever.py`

---

**Q2** 双存储各存什么？  
**A2** JSON：元数据+词表；Chroma：向量

---

**Q3** 全量 rebuild 对 Chroma 的第一步？  
**A3** `reset()`

---

**Q4** 冷启动回填函数名？  
**A4** `_sync_chroma_from_json`

---

**Q5** status 新增三个字段？  
**A5** vector_backend, chroma_path, chroma_count

---

**Q6** 不变量？  
**A6** chroma_count == chunk_count

---

**Q7** 评估为何不用 Chroma？  
**A7** 隔离 A/B，不污染生产

---

**Q8** store.json version？  
**A8** 1.1

---

**Q9** collection 名称？  
**A9** nexus_knowledge

---

**Q10** Day 30 改进什么？  
**A10** 增量 upsert，upload 不 reset

---

**Q11** 分数换算公式？  
**A11** score = 1 - distance (clamp 0-1)

---

**Q12** 需求编号？  
**A12** {REQ}
"""


def _file17() -> str:
    return f"""# Chroma API 速查手册（Day 29）

## ChromaVectorIndex

| 方法 | 签名 | 说明 |
|------|------|------|
| `__init__` | `(persist_path, *, collection_name="nexus_knowledge")` | 延迟连接 |
| `reset` | `() -> None` | 删 collection 并重建 |
| `count` | `() -> int` | 当前向量数 |
| `upsert_chunks` | `(chunks, vectors) -> int` | 批量写入 |
| `query` | `(query_vector, *, top_k=3, min_score=0.05)` | 检索 |
| `delete_by_ids` | `(ids: list[str]) -> int` | 按 id 删 |
| `delete_by_source` | `(source: str) -> int` | 按 metadata 删 |

## ChromaEmbeddingRetriever

| 方法 | 说明 |
|------|------|
| `search(query, *, top_k=3)` | 返回 `list[RetrievalResult]` |
| `chunk_count` | 属性，等同 chroma.count() |

## KnowledgeStore（Day 29 相关）

| 方法 | 说明 |
|------|------|
| `_rebuild_index()` | 全量：fit TF-IDF → reset → upsert |
| `_sync_chroma_from_json()` | chroma 空时回填 |
| `_chroma_index()` | 工厂，解析 chroma_path |
| `status_dict()` | 含 chroma 字段 |

## HTTP

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status | jq '{{vector_backend,chroma_count,chunk_count}}'
```

## 环境变量

| 变量 | 用途 |
|------|------|
| PYTHONPATH=src | 导入路径 |
| NEXUS_LLM_MOCK=1 | 测试 mock LLM |

## 常量

- `VECTOR_BACKEND = "chroma"`  
- `COLLECTION_NAME = "nexus_knowledge"`  
- `STORE_VERSION = "1.1"`  

---

## Python 交互示例

```python
from pathlib import Path
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import KnowledgeStore

store = KnowledgeStore.load_or_bootstrap()
idx = store._chroma_index()
print(idx.count(), store.chunk_count)
```

---

## 错误码与异常（教学）

| 异常 | 场景 |
|------|------|
| ValueError chunks/vectors 不一致 | upsert 参数错误 |
| chromadb 未安装 | import 失败 |
| sqlite locked | 多进程写同 path |

---

## REST 响应示例（status 节选）

```json
{{
  "platform_version": "0.30.0",
  "document_count": 3,
  "chunk_count": 12,
  "vector_backend": "chroma",
  "chroma_path": "/app/data/knowledge/chroma",
  "chroma_count": 12,
  "chunk_config": {{ "chunk_size": 200, "overlap": 40, "strategy": "auto", "name": "default" }},
  "last_rebuilt_at": "2026-08-04T10:00:00Z",
  "index_mode": "full"
}}
```

注：`index_mode` / `last_incremental_at` 字段在 Day 30 增量路径更常用；Day 29 rebuild 后一般为 `full`。

---

## CLI 速查

```bash
# 只看 chroma 字段
curl -s localhost:8000/api/knowledge/status | python3 -m json.tool | grep chroma

# 健康
curl -s localhost:8000/api/health | jq .version
```
"""


def _file18() -> str:
    return f"""# Day 29 与 Day 28 能力对照表

| 能力 | Day 28 | Day 29 | 变化说明 |
|------|--------|--------|----------|
| rebuild_store | ✅ | ✅ | 无修改，内部 _rebuild_index 换实现 |
| 向量存储位置 | store.json | Chroma 目录 | **核心变更** |
| TF-IDF 词表 | JSON | JSON | 不变 |
| upload 索引策略 | 全量 rebuild | 全量 rebuild | 不变（Day 30 改） |
| status API | chunk_count 等 | +chroma 字段 | 扩展 |
| 检索 retriever | EmbeddingRetriever | ChromaEmbeddingRetriever | 换实现 |
| 评估 A/B | 内存 retriever | 内存 retriever | 不变 |
| apply_best_config | ✅ | ✅ | 不变 |
| last_rebuilt_at | ✅ | ✅ | 不变 |
| 平台版本 | 0.28.0 | {VER} | 版本号 |

## 学员常见混淆

**混淆**：「换了 Chroma 就不用 rebuild 了」  
**正解**：rebuild 语义不变，只是向量写入目标从 JSON 改为 Chroma。

**混淆**：「Chroma 可以单独当数据库」  
**正解**：必须以 JSON 为权威源，Chroma 可重建。

## 代码文件对照

| Day 28 重点文件 | Day 29 新增/修改 |
|-----------------|------------------|
| knowledge_rebuild.py | 无改 |
| knowledge_store.py | _rebuild_index, _sync, _build_rag |
| — | chroma_store.py, chroma_retriever.py |

---

## 能力矩阵（细粒度）

| 子能力 | Day 28 | Day 29 |
|--------|--------|--------|
| 解析多格式 | ✅ | ✅ |
| 分块配置 | ✅ | ✅ |
| A/B 评估 | ✅ | ✅（仍内存） |
| 全量 rebuild | ✅ | ✅ |
| 向量持久化 JSON | ✅ | ❌ |
| 向量持久化 Chroma | ❌ | ✅ |
| status chroma 字段 | ❌ | ✅ |
| 增量 upload | ❌ | ❌（Day 30） |
| 混合检索 | ❌ | ❌（Day 31） |

---

## 迁移 FAQ

**问**：Day 28 的作业脚本要改吗？  
**答**：若只调 `rebuild` API，不用改。若直接读 JSON 内向量，需改为调 status 的 `chroma_count` 或 API 检索。

**问**：评估 hit_rate 会变吗？  
**答**：不应变；评估不走 Chroma。若变，说明生产 Chroma 被评估污染，查测试隔离。
"""


def _file19() -> str:
    return f"""# Day 29 讲师补充阅读

## HNSW 简介

Chroma 默认使用 HNSW（Hierarchical Navigable Small World）近似最近邻图。教学规模下与暴力扫描结果接近；规模上万后延迟优势显现。

**参数**（Chroma 内部，本课程不暴露）：

- `M`：每节点最大连接数  
- `efConstruction`：建图宽度  

## SQLite 在 PersistentClient 中的角色

元数据（collection 名、id 列表）存 SQLite；向量存段文件。故「删 chroma 目录」= 完全清空向量索引。

## cosine 与 TF-IDF

TF-IDF 向量经 L2 归一化后，cosine 相似度等价于点积。`EmbeddingClient` 与 Chroma cosine 空间对齐，保证 `test_chroma_matches_in_memory_retriever_top1`。

## 扩展：Chroma Server 模式

生产可启 `chromadb run --path ...` HTTP 服务，多 API 实例共享。教学用 Embedded PersistentClient 降低复杂度。

## 论文推荐

- Malkov & Yashunin, *Efficient and robust approximate nearest neighbor search using HNSW*  
- Chroma 官方 blog: Persistence  

## 安全注意

`documents` 字段含 chunk 明文，磁盘加密与 JSON 同级要求。

---

## FAQ（讲师答疑汇总）

**Q：能否完全去掉 store.json，只用 Chroma？**  
A：不能。文档列表、chunk 正文、TF-IDF 词表是业务权威源；Chroma 仅为向量索引。

**Q：HNSW 参数我们要调吗？**  
A：教学项目不调。Chroma 默认即可；上万 chunk 后再 profiling。

**Q：为何不用 pgvector？**  
A：项目已用 JSON 文件存储元数据，引入 PostgreSQL 是另一套运维；Chroma Embedded 更轻。

**Q：chromadb 0.5 升级要注意什么？**  
A：跑全量 tests/day29+day30；关注 `delete(where=)` 行为。

**Q：多 collection 何时需要？**  
A：多租户隔离时，每租户一 collection；当前单租户 `nexus_knowledge` 足够。

**Q：向量维度存在哪？**  
A：`embedding_state` 中 `dimension` 与 vocab 长度一致；Chroma 不单独存维度元数据。

**Q：CI 如何加速 chromadb 测试？**  
A：tmp_path 隔离 + 镜像预装 wheel；避免每次 pip install。

---

## 数学补充：TF-IDF 向量维度

词表大小 = 向量维度。新词出现 → 维度增加 → 旧向量与新向量长度不一致 → Chroma 无法在同一 collection 内存放（Day 30 因此 reset）。这是 **TF-IDF 增量** 与 **神经网络固定维度 embedding** 的关键差异。

---

## 实验建议

阅读 Chroma 源码外，可用 `chromadb` CLI（若安装）查看 collection stats。对比 Day 30 增量前后 `du -sh chroma/` 变化。
"""


def _file20() -> str:
    return f"""# Day 29 完整代码走查

按调用链顺序阅读，**预计 2 小时**。

## 1. rag/chroma_store.py

`ChromaVectorIndex` — 持久化封装。重点：`reset`, `upsert_chunks`, `query`, `_distance_to_score`。

{fenced("python", CHROMA_STORE[:3500])}

（完整文件见 `22_chroma_store精读.md`）

## 2. rag/chroma_retriever.py

`ChromaEmbeddingRetriever.search` — query embed → chroma.query → 映射 TextChunk。

{fenced("python", CHROMA_RETRIEVER)}

## 3. rag/knowledge_store.py（节选）

### _rebuild_index

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def _rebuild_index"):read_repo(f"{REPO}/rag/knowledge_store.py").find("def _incremental_index")])}

### _sync_chroma_from_json

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def _sync_chroma_from_json"):read_repo(f"{REPO}/rag/knowledge_store.py").find("def _rebuild_index")])}

## 4. 演示脚本

{fenced("python", CHROMA_DEMO)}

## 5. 测试入口

`tests/day29/test_chroma_index.py` — 10 个用例覆盖 upsert、sync、top-1 一致。

`tests/day29/test_chroma_api.py` — status、rebuild、chat。

## 6. 走查检查点

- [ ] 能口述 upsert 的 ids/embeddings/metadatas 来源  
- [ ] 能解释 sync 早退条件  
- [ ] 能画出 chat 请求的检索路径  

---

## 7. rag/embedding.py 与 TF-IDF 状态（节选）

向量编码由 `EmbeddingClient` 完成；`export_state` / `load_state` 与 JSON 词表绑定。

{fenced("python", read_repo(f"{REPO}/rag/embedding.py", limit=120))}

---

## 8. rag/embedding_retriever.py（内存基准）

Chroma 检索必须与以下内存实现对齐：

{fenced("python", read_repo(f"{REPO}/rag/embedding_retriever.py", limit=100))}

---

## 9. api/schemas.py status 字段（节选）

{fenced("python", read_repo(f"{REPO}/api/schemas.py", limit=80))}

---

## 10. 逐步调试指南

### 10.1 断点 1：_rebuild_index 入口

确认 `len(self.chunks)` 与预期一致；空库应 `reset` 后不 upsert。

### 10.2 断点 2：upsert_chunks 返回

返回值应等于 `len(chunks)`；随后 `chroma.count()` 相同。

### 10.3 断点 3：ChromaEmbeddingRetriever.search

检查 `model.is_fitted`；未加载词表时返回空列表。

### 10.4 断点 4：API status

`status_dict()` 合并 store 与 chroma 字段，无缓存陈旧值。

---

## 11. 文件依赖图（ASCII）

```
day29/chroma_demo.py
    └── knowledge_store.KnowledgeStore
            ├── chroma_store.ChromaVectorIndex
            ├── chroma_retriever.ChromaEmbeddingRetriever
            └── embedding_retriever.EmbeddingRetriever (rebuild only)

tests/day29/*
    └── 同上 + fastapi TestClient
```

---

## 12. 走查测验（自评）

完成走查后闭卷回答：

1. 列出 upsert 时写入 Chroma 的四类 payload 字段名。  
2. `_sync_chroma_from_json` 哪一行决定「不重复 embed」？  
3. rebuild 后 `index_mode` 是什么？（Day 30 字段，Day 29 已写入）  
4. 为何 `ChromaEmbeddingRetriever` 仍要传入全量 `chunks` 列表？  

**参考答**：需用 `chunk_id` 映射回 `TextChunk` 正文与 offset；Chroma 仅返回 id/score/metadata，完整 RAG 上下文依赖 JSON chunks。

---

## 13. knowledge_store 全文索引（选读）

以下嵌入 `knowledge_store.py` 全文供交叉检索，走查时配合 IDE 折叠阅读。

{fenced("python", KNOWLEDGE_STORE[:12000])}

（余下部分见仓库 `src/rag/knowledge_store.py`）
"""


def _file21() -> str:
    return f"""# Day 29 课堂知识竞赛

**规则**：15 题，抢答，答对 +10 分，答错 -5 分。

1. **Chroma collection 叫什么名字？** → `nexus_knowledge`

2. **VECTOR_BACKEND 常量值？** → `chroma`

3. **store.json 版本号？** → `1.1`

4. **全量 rebuild 前对 Chroma 调用什么？** → `reset()`

5. **冷启动同步函数？** → `_sync_chroma_from_json`

6. **相似度如何从 distance 计算？** → `1 - distance`

7. **status 里向量数叫什么字段？** → `chroma_count`

8. **词表存在哪？** → `store.json` 的 `embedding`

9. **Day 29 测试目录？** → `tests/day29/`

10. **评估模块用不用 Chroma？** → 不用

11. **Chroma 持久化默认子目录？** → `data/knowledge/chroma`

12. **需求编号？** → {REQ}

13. **演示脚本之一？** → `chroma_demo.py`

14. **双存储不变量？** → chroma_count == chunk_count

15. **Day 30 主题？** → 增量索引

## 加分题

现场运行 `python3 src/day29/chroma_demo.py` 并读出 `chroma_count`，+20 分。

---

## 竞赛附录：题目解析课稿

**第 1 题** collection 名固定 `nexus_knowledge`，避免多项目共目录时冲突。  

**第 4 题** reset 是全量 rebuild 语义核心；与 Day 30 incremental 对比是明日高潮。  

**第 8 题** 词表必须在 JSON，因为 query 编码与文档编码须同一 vocab/idf。  

**第 14 题** 不变量是运维巡检第一指标。  

---

## 第二轮抢答（备用 10 题）

1. `PersistentClient` 第一个参数？ → `path`  
2. Chroma 返回距离类型？ → float distance  
3. `_chroma_index()` 解析的路径字段？ → chroma_path 或默认 knowledge_chroma  
4. ingest 非增量时调用的索引方法？ → `_rebuild_index`  
5. `STORE_VERSION` 值？ → 1.1  
6. 测试中 `_store(tmp_path)` 作用？ → 隔离路径  
7. `rebuild_store` 在何文件？ → knowledge_rebuild.py  
8. RAG 服务构建方法？ → `_build_rag_service`  
9. chroma 遥测设置字段？ → anonymized_telemetry  
10. Phase 3 第五日主题？ → Chroma 向量库  
"""


def _file22() -> str:
    return f"""# Day 29 精读：chroma_store.py 与 chroma_retriever.py

**需求**：{REQ} | **建议学时**：90 分钟  
本课全文嵌入仓库**真实源码**，请对照 IDE 单行调试。

---

## 一、模块职责

`chroma_store.py` 隔离 `chromadb` 第三方 API，向上提供稳定的 `ChromaVectorIndex`。`chroma_retriever.py` 实现与 `EmbeddingRetriever` 相同的检索端口，供 `DocumentIndex` 无感切换。

---

## 二、chroma_store.py 完整源码

{fenced("python", CHROMA_STORE)}

---

## 三、逐段讲解

### 3.1 延迟 import（L54–65）

```python
def _ensure_client(self) -> Any:
    if self._client is not None:
        return self._client
    import chromadb
```

**原因**：未安装 chromadb 时，仅 import `knowledge_store` 不立刻失败；真正访问 Chroma 才报错。测试可 mock。

### 3.2 reset()（L77–85）

`delete_collection` 吞掉「不存在」异常，然后 `_collection = None` 再 `_ensure_collection()`。**必须**重建句柄，否则 upsert 到已删 collection。

### 3.3 upsert_chunks（L90–120）

- `ids` 使用业务主键 `chunk_id`，保证跨 rebuild 可追踪（同内容同 id 策略由 chunker 决定）  
- `documents` 存原文方便 `chromadb` CLI 调试  
- `metadatas` 的 `source` 供 Day 30 `delete_by_source`  

### 3.4 query（L148–186）

`n_results = max(1, min(top_k, collection.count()))` 避免空库或 top_k 过大报错。排序：`(-score, index)` 稳定 tie-break。

### 3.5 delete_by_ids / delete_by_source（L122–146）

Day 29 已实现，Day 30 增量替换同名文档时调用。`delete_by_source` 先 `get(where=...)` 再 `delete(ids=...)`，兼容不同 chromadb 版本。

---

## 四、chroma_retriever.py 完整源码

{fenced("python", CHROMA_RETRIEVER)}

### 4.1 _chunks_by_id 字典

O(1) 由 `chunk_id` 取 `TextChunk`。若 Chroma 命中 id 在 JSON 中不存在（不一致），**跳过**该 hit，防止脏数据。

### 4.2 model.is_fitted 检查

词表未加载时返回 `[]`，与 `EmbeddingRetriever` 一致。

### 4.3 _overlap_terms

保留 matched_tokens 供前端高亮，与内存 retriever 行为一致。

---

## 五、与 KnowledgeStore 的接点

```python
# knowledge_store._rebuild_index 核心四行
retriever = EmbeddingRetriever(self.chunks)
self.embedding_state = retriever._client.model.export_state()
vectors = retriever._client.embed_batch([c.text for c in self.chunks])
chroma.reset()
chroma.upsert_chunks(self.chunks, vectors)
```

---

## 六、调试练习

1. 在 `upsert_chunks` 打日志，打印 `len(ids)` 与 `chroma.count()`  
2. 修改 `min_score=0.99`，观察 search 返回空列表  
3. 对比 `EmbeddingRetriever` 与 `ChromaEmbeddingRetriever` 同一 query 的 top-3  

---

## 七、自检问题

1. 为何 `upsert` 而不是 `add`？  
2. `ChromaHit` 与 `RetrievalResult` 为何分两层？  
3. 若 `distance` 为 NaN 会怎样？（`_distance_to_score` clamp 能否处理？）

---

## 十二、chroma_store.py 逐行精读表

| 行号区间 | 代码职责 | 讲师点评 |
|----------|----------|----------|
| L1–8 | 模块 docstring | 标明 REQ-029/030 双需求：删除 API 为 Day 30 预埋 |
| L19–20 | COLLECTION_NAME / VECTOR_BACKEND | 常量供测试与 status 断言 |
| L23–29 | ChromaHit dataclass | 比 RetrievalResult 更贴近 Chroma 原生返回 |
| L32–52 | __init__ 延迟连接 | persist_path 可测试注入 |
| L54–65 | _ensure_client | 延迟 import chromadb；mkdir；关遥测 |
| L67–75 | _ensure_collection | cosine 空间在此固定，全库一致 |
| L77–85 | reset | 全量 rebuild 入口；吞 delete 异常防首次空库报错 |
| L87–88 | count | 运维健康检查核心 |
| L90–120 | upsert_chunks | 四列表对齐；ValueError Guard |
| L122–128 | delete_by_ids | Day 30 同名替换删旧 chunk |
| L130–146 | delete_by_source | metadata 过滤；兼容多版本 API |
| L148–186 | query | n_results 边界；min_score 过滤；排序稳定 |
| L189–191 | _distance_to_score | 纯函数，便于单测 |

建议学员用 IDE「跳转定义」对照本表，每行加断点观察一次 query 全流程。

---

## 十三、chroma_retriever 与 DocumentIndex 契约

`DocumentIndex.retrieve` 不关心向量来自内存还是 Chroma，仅调用 `self._retriever.search`。因此 Day 29 切换 retriever 后，`RAGContextService` 与 `api/chat` **零修改**。这是端口适配器模式的典型案例。

---

## 十四、课后重构题（不提交）

若将 `ChromaVectorIndex` 改为抽象基类 `VectorIndexBase`，列出子类需实现的 6 个方法。思考：Day 31 混合检索是否需扩展接口？

---

## 八、knowledge_store.py 集成节选（真实源码）

### 8.1 模块头与常量

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py", limit=35))}

### 8.2 ingest_parsed 非增量分支（Day 29 upload 仍走此路径）

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def ingest_parsed"):read_repo(f"{REPO}/rag/knowledge_store.py").find("def save")][:2800])}

### 8.3 load 与 _sync 调用点

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def load"):read_repo(f"{REPO}/rag/knowledge_store.py").find("def load_or_bootstrap")])}

### 8.4 _build_rag_service 完整实现

{fenced("python", read_repo(f"{REPO}/rag/knowledge_store.py")[read_repo(f"{REPO}/rag/knowledge_store.py").find("def _build_rag_service"):read_repo(f"{REPO}/rag/knowledge_store.py").find("_store:")])}

---

## 九、test_chroma_index.py 全文走读

{fenced("python", TEST_CHROMA_INDEX)}

### 9.1 测试夹具 _store

每个测试用 `tmp_path` 隔离 `store.json` 与 `chroma/`，避免污染开发者默认 `data/knowledge/`。`bootstrap_from_sample_docs` 保证有 sample 块可检索。

### 9.2 test_load_restores_chroma_from_json

证明「仅删 chroma 不删 JSON」时 load 能恢复 count。这是运维事故最常见场景。

### 9.3 test_empty_store_clears_chroma

空库必须 `chroma.count()==0`，防止脏向量残留影响「空库」语义。

---

## 十、与 EmbeddingRetriever 的接口契约

| 方法 | EmbeddingRetriever | ChromaEmbeddingRetriever |
|------|-------------------|------------------------|
| search(query, top_k=3) | ✅ | ✅ |
| chunk_count | len(chunks) | chroma.count() |
| 依赖 | 内存向量列表 | Chroma + chunks 字典 |

`DocumentIndex` 只依赖 `search` 返回 `RetrievalResult`，故切换 retriever 不改上层 RAG 代码。

---

## 十一、延伸阅读代码路径

- `rag/embedding_retriever.py` — 内存检索基准  
- `rag/context.py` — DocumentIndex.retrieve  
- `core/paths.py` — knowledge_chroma 路径注册  
- `api/schemas.py` — KnowledgeStatusResponse 字段定义  
"""


def _file23() -> str:
    return f"""# 双存储与迁移策略（Day 29 实践指南）

## 1. 权威源与重建

| 场景 | 权威 | 操作 |
|------|------|------|
| 文档增删改 | JSON chunks | upload/rebuild 更新 JSON 后索引 Chroma |
| 向量损坏 | JSON + 词表 | `_rebuild_index` 或 `_sync_chroma_from_json` |
| Chroma 全丢 | JSON | load 自动 sync |
| JSON 全丢 | 无法恢复 | 从备份恢复 |

## 2. _sync_chroma_from_json 详解

```python
if chroma.count() > 0:
    return  # 早退：已有数据不覆盖
```

**设计意图**：避免每次 load 重复 embed 全库（昂贵）。若 JSON chunks 变更但 Chroma 仍有旧数据，count 可能仍相等但内容错——此时须 **rebuild**。

## 3. 迁移检查清单

1. 部署新版本前备份 `store.json` + `chroma/`  
2. 部署后 `GET status` 检查 `chroma_count`  
3. 跑 `pytest tests/day29/ -q`  
4. 抽样 chat 查询  

## 4. 多环境路径

| 环境 | chroma_path |
|------|-------------|
| 本地 | data/knowledge/chroma |
| CI tmp | tmp_path / chroma |
| 测试注入 | store.chroma_path = ... |

## 5. 与 Day 30 衔接

Day 30 upload 走 `_incremental_index`，**不** reset。双存储不变量仍成立，但词表扩张时需特殊处理（见 Day 30 课件）。

---

## 6. 迁移剧本：从纯 JSON 到双存储（分步）

### 步骤 1：部署 {VER} 代码，旧 data 不动

### 步骤 2：首次 `load_or_bootstrap`

若 chroma 空，`_sync_chroma_from_json` 自动 embed 全库（可能耗时数秒）。

### 步骤 3：验证 status

`chroma_count == chunk_count`，抽样 chat。

### 步骤 4：可选 `POST rebuild`

确保 chunk 与源文件一致，非必须若数据已净。

### 步骤 5：归档旧 JSON 备份

保留升级前 tar 至少 30 天。

---

## 7. 反模式（Anti-patterns）

| 反模式 | 后果 |
|--------|------|
| 只 git store.json | chroma 丢则冷启动需 re-embed |
| 手改 chroma sqlite | 损坏难修复 |
| 多环境共 chroma 目录 | 数据互踩 |
| 跳过 top-1 测试发版 | 检索 silently wrong |

---

## 8. Runbook 片段（运维）

```bash
# 健康检查
python3 scripts/chroma_health.py || echo "ALERT"

# 强制重建
curl -X POST localhost:8000/api/knowledge/rebuild -H 'Content-Type: application/json' \\
  -d '{{"include_sample_docs": true}}'

# 备份
tar czf /backup/knowledge-$(date +%s).tar.gz data/knowledge/store.json data/knowledge/chroma
```
"""


def _file24() -> str:
    return f"""# Phase 3 第五日总结（Day 25–29）

## 进度条

| Day | 主题 | 版本 |
|-----|------|------|
| 25 | KnowledgeStore MVP | 0.25.0 |
| 26 | Markdown/PDF 解析 | 0.26.0 |
| 27 | 分块调参 A/B | 0.27.0 |
| 28 | 全量 rebuild | 0.28.0 |
| 29 | Chroma 向量库 | {VER} |

## Day 29 在 Phase 3 的位置

**基础设施层**从「单文件 JSON」升级为「JSON + 向量库双存储」，为 Day 30 增量索引、Day 31 混合检索打地基。

## 关键技能树

```
KnowledgeStore
├── ingest / save / load
├── _rebuild_index  ──→  Chroma reset + upsert
├── _sync_chroma_from_json
└── as_rag_service  ──→  ChromaEmbeddingRetriever
```

## 团队贡献

- 陈默：架构与 PRD  
- 林晓：chroma_store + store 集成  
- 周航：15 项测试 + CI  
- 赵岩：运维备份 SOP  

## 明日 Day 30

upload 增量、同名替换、`index_mode` 字段。请预习 `27_Day30增量索引预习.md`。

---

## Day 25–29 代码行数成长（示意）

| Day | 新增核心文件 | 测试数 |
|-----|-------------|--------|
| 25 | knowledge_store | 12 |
| 26 | doc_parser, chunk_strategies | 17 |
| 27 | chunk_config, retrieval_eval | 15 |
| 28 | knowledge_rebuild | 14 |
| 29 | chroma_store, chroma_retriever | 15 |

Phase 3 知识库栈已具 **存-读-调-发-索引** 闭环。

---

## 知识自检 20 问（Phase 3 综合）

1. KnowledgeStore 权威数据源？  
2. rebuild 与 evaluate 区别？  
3. chunk_config 何时生效？  
4. uploads 与 sample 优先级？  
5. Chroma 存什么不存什么？  
6. ……（教师可口播其余 15 问）

---

## 致谢

感谢产品部提供真实 PDF 样例，运维部提供备份窗口，QA 通宵跑 regression。
"""


def _file25() -> str:
    return f"""# Day 29 精读：chroma_api_demo.py 与 API 测试

## chroma_api_demo.py 全文

{fenced("python", CHROMA_API_DEMO)}

## 脚本逻辑

1. `set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())` — 注入全局单例  
2. `TestClient(create_app())` — 无需起 uvicorn  
3. 打印 status 的 `vector_backend` / `chroma_count`  
4. `POST /api/knowledge/rebuild` 验证重建后块数  
5. `POST /api/chat` 验证检索链路  
6. `GET /api/health` 读版本号  

## test_chroma_api.py 全文

{fenced("python", TEST_CHROMA_API)}

## 断言设计点评

- `test_health_version`：平台版本与发版一致  
- `test_status_includes_chroma_fields`：`chroma_count == chunk_count`  
- `test_rebuild_keeps_chroma_in_sync`：rebuild 后仍相等  
- `test_chat_after_chroma_index`：端到端  
- `test_upload_updates_chroma_count`：Day 29 upload 仍全量，但 chroma 同步  

## curl 等价命令

```bash
curl -s http://127.0.0.1:8000/api/knowledge/status
curl -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' -d '{{"include_sample_docs": true}}'
curl -X POST http://127.0.0.1:8000/api/chat \\
  -H 'Content-Type: application/json' -d '{{"message": "产品收益？"}}'
```

---

## incremental_api 对比说明（Day 30 预习）

Day 29 的 `test_upload_updates_chroma_count` 验证 upload 后 chroma 仍同步，但**不**验证 reset 未调用——那是 Day 30 `test_incremental_api` 的职责。阅读本测试时注意：Day 29 upload 仍会触发全量 `_rebuild_index`。

---

## Mock 与 TestClient 模式

`chroma_api_demo` 与测试均用 `TestClient` 而非真实 uvicorn，原因：

1. 启动快，适合 CI  
2. 同步调用，不断言端口  
3. `set_knowledge_store` 注入隔离数据  

生产环境行为一致，除非 middleware 依赖真实 ASGI 生命周期。

---

## 字段断言清单（教师）

| 测试 | 关键断言 |
|------|----------|
| test_health_version | version == 平台发版号 |
| test_status_includes_chroma_fields | chroma_count == chunk_count |
| test_rebuild_keeps_chroma_in_sync | rebuild 后仍相等 |
| test_chat_after_chroma_index | reply 非空 |
| test_upload_updates_chroma_count | upload 后仍相等 |
"""


def _file26() -> str:
    return f"""# Day 29 实操 Lab 手册

**学时**：120 分钟 | **环境**：nexus-agent-platform | **需求**：{REQ}

## 前置条件

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1
```

---

## Step 1：Bootstrap 与 status 基线（15 min）

```bash
python3 src/day29/chroma_demo.py
```

**记录**：`vector_backend`, `chunk_count`, `chroma_count`。  
**期望**：三者满足 backend=chroma 且 count 相等。

---

## Step 2：检查 Chroma 落盘目录（10 min）

```bash
ls -la data/knowledge/chroma/
```

**期望**：存在 `chroma.sqlite3` 等文件。  
**思考**：这些文件与 `store.json` 的关系？

---

## Step 3：rebuild 实验（20 min）

```bash
python3 src/day29/chroma_api_demo.py
```

或手动：

```bash
curl -s -X POST http://127.0.0.1:8000/api/knowledge/rebuild \\
  -H 'Content-Type: application/json' -d '{{"include_sample_docs": true}}' | jq .
```

**记录**：`chunks_before`, `chunks_after`, rebuild 后 `chroma_count`。

---

## Step 4：删除 chroma 目录冷启动（25 min）

```bash
rm -rf data/knowledge/chroma
python3 -c "
from rag.knowledge_store import KnowledgeStore
s = KnowledgeStore.load_or_bootstrap()
st = s.status_dict()
print('chroma_count', st['chroma_count'], 'chunk_count', st['chunk_count'])
"
```

**期望**：`chroma_count` 自动恢复等于 `chunk_count`。  
**原理**：`_sync_chroma_from_json`。

---

## Step 5：测试套件（30 min）

```bash
python3 -m pytest tests/day29/test_chroma_index.py -v
python3 -m pytest tests/day29/test_chroma_api.py -v
```

**重点阅读**：`test_chroma_matches_in_memory_retriever_top1` 源码。

{fenced("python", read_repo(f"{REPO}/../tests/day29/test_chroma_index.py")[read_repo(f"{REPO}/../tests/day29/test_chroma_index.py").find("def test_chroma_matches"):])}

---

## Step 6：实验报告（20 min）

撰写 Markdown，包含：

1. 五步命令输出摘要  
2. 删 chroma 前后对比表  
3. 双存储架构自手绘图照片  
4. 一条你踩的坑  

**提交**：`lab/day29-<姓名>.md`

---

## 附录 A：故障注入实验（选做 30 min）

### A.1 人为制造 count 不一致

```bash
python3 -c "
from pathlib import Path
from rag.knowledge_store import KnowledgeStore
from rag.chroma_store import ChromaVectorIndex
s = KnowledgeStore.load_or_bootstrap()
c = ChromaVectorIndex(s._resolve_chroma_path())
# 仅删除一个 id（若库非空）
if c.count() > 0:
    col = c._ensure_collection()
    ids = col.get(include=[])['ids']
    if ids:
        c.delete_by_ids([ids[0]])
        print('deleted one, chroma', c.count(), 'chunks', s.chunk_count)
"
```

运行作业 A 健康检查脚本，应报警。再 `POST rebuild` 修复。

### A.2 对比内存与 Chroma 延迟（粗略）

```bash
python3 -c "
import time
from rag.knowledge_store import KnowledgeStore
from rag.embedding_retriever import EmbeddingRetriever
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.embedding import EmbeddingClient
s = KnowledgeStore.load_or_bootstrap()
q = '年化收益率'
mem = EmbeddingRetriever(s.chunks)
t0=time.perf_counter()
mem.search(q, top_k=3)
t1=time.perf_counter()
client = EmbeddingClient()
client.model.load_state(s.embedding_state)
ch = ChromaEmbeddingRetriever(s.chunks, s._chroma_index(), client=client)
t2=time.perf_counter()
ch.search(q, top_k=3)
t3=time.perf_counter()
print('mem ms', (t1-t0)*1000, 'chroma ms', (t3-t2)*1000)
"
```

教学规模两者接近；记录结果写入实验报告「观察」小节。

---

## 附录 B：Lab 评分 Rubric

| 项 | 优秀 | 及格 | 不及格 |
|----|------|------|--------|
| Step 1–5 命令完整 | 全部可复现 | 缺 1 步 | 缺 ≥2 步 |
| 删 chroma 实验 | 有前后对比表 | 仅文字描述 | 未做 |
| 原理说明 | 能解释 sync | 复述课件 | 错误 |
| 踩坑记录 | 真实具体 | 泛泛 | 无 |

---

## 附录 C：常用路径与环境

| 项 | 路径 |
|----|------|
| 默认 store | data/knowledge/store.json |
| 默认 chroma | data/knowledge/chroma |
| 源码 chroma_store | src/rag/chroma_store.py |
| 测试 | tests/day29/ |
| 演示 | src/day29/chroma_demo.py |

Windows 学员请注意：路径分隔符与 `rm -rf` 替换为 PowerShell 等价命令。
"""


def _file27() -> str:
    return f"""# Day 30 预习：增量索引（incremental upsert）

**明日需求**：ZL-NA-REQ-030 | **版本**：v0.30.0

## 今日痛点（Day 29）

每次 `POST /api/knowledge/upload`，`KnowledgeStore` 仍调用 `_rebuild_index()` → `chroma.reset()` 全库重建。上传一份公告却重写全部向量，**运营不可接受**。

## 明日目标

| 操作 | Day 29 | Day 30 |
|------|--------|--------|
| upload | 全量 rebuild + reset | `_incremental_index`，仅 upsert |
| rebuild | 全量 reset | 不变 |
| 同名 re-upload | 可能重复文档 | `_remove_document_by_source` |

## 预习阅读

1. `ChromaVectorIndex.delete_by_ids` — Day 29 已实现  
2. `knowledge_store.ingest_parsed(..., incremental=True)` 分支  
3. 思考：新文档带来**新 TF-IDF 词**时，向量维度变化，Chroma 能否只 upsert 新 chunk？  

## 陈默预告

> 「今天学会了换引擎，明天学会换节奏 —— 增量比全量更贴近生产。」

## 预习作业

列出 `_incremental_index` 你可能写的 5 个步骤（不必正确，上课对比）。

---

## Day 30 详细预告（陈默邮件摘录）

> 团队好，  
> Day 30（ZL-NA-REQ-030）焦点是 **upload 默认 incremental**。  
> 关键难点：新文档引入新 TF-IDF 词时，向量**维度**变化，Chroma 不能只对单 chunk upsert——必须 `reset()` 后全量 upsert 所有 chunk。同内容 re-upload 则仅 upsert 不 reset。  
> 请今晚阅读 `knowledge_store._incremental_index` 源码草稿。  
> ——陈默

---

## 概念对比表

| 概念 | Day 29 | Day 30 |
|------|--------|--------|
| upload 索引 | _rebuild_index + reset | _incremental_index |
| 同名文件 | 可能重复（若未删旧） | _remove_document_by_source |
| index_mode | 多为 full | incremental |
| vocab 扩张 | 全量 rebuild 自然处理 | 触发 chroma reset + 全量 upsert |

---

## 自测：你真的理解 Day 29 了吗？

1. 不看笔记，写出 `_rebuild_index` 四步。  
2. 解释为何 JSON 仍保留 embedding_state。  
3. 若明日 upload 不 reset，今日学的 `delete_by_ids` 用在哪？（提示：同名替换）
"""


if __name__ == "__main__":
    build()
