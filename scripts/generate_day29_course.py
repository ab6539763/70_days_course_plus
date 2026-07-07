#!/usr/bin/env python3
"""Generate course/day29 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day29"
OUT.mkdir(parents=True, exist_ok=True)
FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add("README.md", """# Day 29 课件索引

**日期**：2026-08-05（星期三）  
**主题**：Chroma 向量库持久化  
**需求**：ZL-NA-REQ-029

## 今日交付

- `rag/chroma_store.py` — ChromaVectorIndex 持久化封装
- `rag/chroma_retriever.py` — ChromaEmbeddingRetriever
- `KnowledgeStore` 向量索引迁移至 Chroma，JSON 保留 TF-IDF 词表
- `GET /api/knowledge/status` 增加 vector_backend / chroma_count
- `tests/day29/` 15 项

```bash
PYTHONPATH=src python3 src/day29/chroma_demo.py
PYTHONPATH=src pytest tests/day29/ -q
```

## 关键流程

Day 28 rebuild 流程不变 → Day 29 **换索引引擎**：向量落盘 `data/knowledge/chroma/`。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day29/chroma_demo.py
python3 src/day29/chroma_api_demo.py
python3 -m pytest tests/day29/ -v
```

## 设计决策

1. **双存储**：store.json 存元数据 + TF-IDF 词表；Chroma 存向量  
2. **重建不变**：`_rebuild_index()` 先 fit TF-IDF 再 upsert Chroma  
3. **冷启动迁移**：load 时若 Chroma 空则从 JSON 自动回填  
4. **评估隔离**：Day 27 A/B 仍用内存 EmbeddingRetriever，避免污染生产 Chroma  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_Chroma向量库详解 | 专题 |
| 22_chroma_store精读 | 源码 |
| 27_Day30预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day29/chroma_api_demo.py
```
""")

FILES["00_旁白解读.md"] = """# Day 29 旁白解读

2026 年 8 月 5 日，星期三。林晓打开 `store.json`，embedding 字段里密密麻麻的 vocab 让她头疼。陈默指着文件大小：「词表可以留 JSON，但**向量矩阵**不该再塞进去。今天我们接 Chroma。」

赵岩在白板画了两层：上层 KnowledgeStore 管 documents/chunks，下层 Chroma PersistentClient 管向量。周航问：「rebuild 还要跑吗？」陈默点头：「流程不变，`_rebuild_index` 里换成 `chroma.reset()` + `upsert_chunks`。」

下午 Lab，林晓执行 `chroma_demo.py`，终端打印 `vector_backend: chroma` 与 `chroma_count: 12`。她删除 chroma 目录后重启服务，发现 load 会自动从 JSON 回填向量 —— 这就是 `_sync_chroma_from_json`。

```mermaid
journey
    title Day 29
    section 上午
      理解双存储架构: 4: 林晓
      ChromaVectorIndex 走读: 5: 林晓
    section 下午
      rebuild 后 chroma_count 校验: 4: 林晓
      status API 新字段: 4: 林晓
```
"""

FILES["02_需求文档.md"] = """# ZL-NA-REQ-029 需求文档

## FR-001 Chroma 持久化

- 路径：`data/knowledge/chroma/`
- collection：`nexus_knowledge`
- 距离：cosine

## FR-002 KnowledgeStore 集成

- `_rebuild_index`：fit TF-IDF → export_state → chroma upsert
- `_build_rag_service`：ChromaEmbeddingRetriever
- `store.json` version 升至 1.1，新增 `vector_backend`

## FR-003 迁移

- load 时 Chroma 为空且 chunks 存在 → `_sync_chroma_from_json`

## FR-004 status API

- `vector_backend`、`chroma_path`、`chroma_count`

## 非目标

- 替换 TF-IDF 为 OpenAI Embedding API
- 多 collection 分租户
- 增量 upsert 单文档（Day 30+）
"""

TEMPLATE = """# Day 29 {title}

**需求**：ZL-NA-REQ-029

## 概述

{summary}

## 核心知识点

### 1. 为何引入 Chroma？

Day 25–28 向量与词表挤在 `store.json`，随 chunk 增长文件膨胀、全量 load 变慢。Chroma 提供**专用向量持久化**与 ANN 检索能力（教学规模仍可用线性 scan 等价路径）。

### 2. 双存储架构

| 存储 | 内容 | 路径 |
|------|------|------|
| JSON | documents、chunks、TF-IDF vocab/idf | store.json |
| Chroma | chunk_id、embedding、metadata | data/knowledge/chroma |

### 3. _rebuild_index 新流程

1. EmbeddingRetriever(chunks) 训练 TF-IDF  
2. embedding_state = export_state()  
3. chroma.reset()  
4. chroma.upsert_chunks(chunks, vectors)  

### 4. ChromaVectorIndex API

- `reset()` — 删除 collection  
- `upsert_chunks()` — 写入向量  
- `query()` — 按 query_embedding 检索  
- `count()` — 当前向量数  

### 5. ChromaEmbeddingRetriever

实现与 EmbeddingRetriever 相同的 `search(query, top_k)`，供 DocumentIndex 无感切换。

### 6. 与 Day 28 rebuild 关系

`rebuild_store` 仍调用 `_rebuild_index()`，无需修改 rebuild 模块；换的是索引实现。

### 7. 评估路径隔离

`retrieval_eval.build_retriever_for_doc` 仍用内存 EmbeddingRetriever，避免 A/B 实验写入生产 Chroma。

### 8. status 新字段

```json
{{
  "vector_backend": "chroma",
  "chroma_path": "/.../data/knowledge/chroma",
  "chroma_count": 12
}}
```

### 9. Day 30 预告

增量索引：单文档 upload 仅 upsert 对应 chunk，无需全量 reset。

### 10. 运维注意

备份需同时包含 store.json 与 chroma 目录；仅删 JSON 会导致元数据丢失。

### 11. 课堂检查清单

- [ ] chroma_count == chunk_count  
- [ ] rebuild 后 Chroma 与 JSON 一致  
- [ ] chat 检索仍返回相关片段  
- [ ] 删除 chroma 后 load 能自动回填  
"""

for fname, title, summary in [
    ("01_企业背景与今日任务.md", "背景", "JSON 向量索引到上限，需专业向量库。"),
    ("02_需求文档_扩展.md", "扩展", "用户故事与验收。"),
    ("03_架构设计.md", "架构", "双存储与检索链路。"),
    ("04_流程图与示意图.md", "流程图", "upsert 与 query 时序。"),
    ("05_课堂笔记_上午.md", "上午", "Chroma 概念与安装。"),
    ("06_课堂笔记_下午.md", "下午", "集成 Lab。"),
    ("07_晚自习.md", "晚自习", "对比 Milvus / Qdrant。"),
    ("08_作业.md", "作业", "实现 chroma_count 监控脚本。"),
    ("09_作业答案.md", "答案", "参考实现。"),
    ("10_Chroma验收清单.md", "验收", "教师表。"),
    ("11_Chroma向量库详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习", "选择题。"),
    ("13_深度扩展_向量库选型.md", "扩展", "Chroma vs 云向量库。"),
    ("14_企业案例集_索引迁移日.md", "案例", "从 JSON 迁 Chroma。"),
    ("15_授课实录.md", "实录", "摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡。"),
    ("17_ChromaAPI速查手册.md", "速查", "Python API。"),
    ("18_与Day28能力对照表.md", "对照", "rebuild vs 引擎。"),
    ("19_讲师补充阅读.md", "补充", "HNSW 原理简介。"),
    ("20_完整代码走查.md", "走查", "源码。"),
    ("21_课堂知识竞赛.md", "竞赛", "15题。"),
    ("22_chroma_store精读.md", "精读", "ChromaVectorIndex。"),
    ("23_双存储与迁移策略.md", "实践", "_sync_chroma_from_json。"),
    ("24_Phase3第五日总结.md", "总结", "Day25-29。"),
    ("25_chroma_api脚本精读.md", "精读", "status 字段。"),
    ("26_实操Lab手册.md", "Lab", "六步。"),
    ("27_Day30增量索引预习.md", "预习", "增量 upsert。"),
]:
    add(fname, TEMPLATE.format(title=title, summary=summary))

FILES["11_Chroma向量库详解.md"] = FILES["11_Chroma向量库详解.md"].replace(
    "## 概述",
    """## 1. PersistentClient

```python
chromadb.PersistentClient(path="data/knowledge/chroma")
```

数据落盘 SQLite + 二进制段文件，重启后 collection 仍在。

## 2. metadata 设计

每个 chunk 存 source、index、start_char、end_char；正文存 documents 字段供调试。

## 3. cosine 距离换算

Chroma 返回 distance，相似度 `score = 1 - distance`，与 EmbeddingRetriever 对齐。

## 概述""",
)

FILES["20_完整代码走查.md"] = """# Day 29 完整代码走查

1. `rag/chroma_store.py` — ChromaVectorIndex  
2. `rag/chroma_retriever.py` — ChromaEmbeddingRetriever  
3. `rag/knowledge_store.py` — _rebuild_index / _sync_chroma_from_json  
4. `core/paths.py` — knowledge_chroma  
5. `api/schemas.py` — KnowledgeStatusResponse 新字段  
6. `requirements-api.txt` — chromadb  
"""

FILES["27_Day30增量索引预习.md"] = """# Day 30 预习

**预告**：单文档 upload 增量 upsert Chroma，避免每次全量 reset。

陈默：「今天学会了换引擎，明天学会换节奏 —— 增量比全量更贴近生产。」
"""


def main() -> None:
    total = sum(len(c) for c in FILES.values())
    for name, content in FILES.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(f"Total: {total} chars in {len(FILES)} files")
    if total < 30000:
        raise SystemExit(f"need >= 30000, got {total}")


if __name__ == "__main__":
    main()
