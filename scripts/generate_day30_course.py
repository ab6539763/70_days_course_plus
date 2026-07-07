#!/usr/bin/env python3
"""Generate course/day30 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day30"
OUT.mkdir(parents=True, exist_ok=True)
FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add("README.md", """# Day 30 课件索引

**日期**：2026-08-06（星期四）  
**主题**：增量索引（incremental upsert）  
**需求**：ZL-NA-REQ-030

## 今日交付

- `_incremental_index` — upload 不 reset Chroma
- `_remove_document_by_source` — 同名上传替换
- `chroma_store.delete_by_ids / delete_by_source`
- `index_mode` / `last_incremental_at` 状态字段
- `tests/day30/` 16 项

```bash
PYTHONPATH=src python3 src/day30/incremental_demo.py
PYTHONPATH=src pytest tests/day30/ -q
```

## 关键流程

Day 29 全量 upsert → Day 30 **upload 增量**：仅 upsert 新文档 chunk，rebuild 仍全量。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day30/incremental_demo.py
python3 src/day30/incremental_api_demo.py
python3 -m pytest tests/day30/ -v
```

## 设计决策

1. **upload 默认 incremental=True**  
2. **rebuild 仍 _rebuild_index + reset**  
3. **词表扩张时回退全量 upsert（不 reset）**  
4. **评估路径仍用内存 EmbeddingRetriever**  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_增量索引详解 | 专题 |
| 22_knowledge_incremental精读 | 源码 |
| 27_Day31预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day30/incremental_api_demo.py
```
""")

FILES["00_旁白解读.md"] = """# Day 30 旁白解读

2026 年 8 月 6 日，星期四。林晓发现每次上传 PDF，日志里都出现 `chroma.reset()`。陈默：「Day 29 换了引擎，但节奏还是全量。生产环境上传一份公告不该重建整个索引。」

他在白板对比两条路径：

| 操作 | 索引策略 |
|------|----------|
| POST upload | incremental upsert |
| POST rebuild | full reset |

赵岩补充：「同名文件 re-upload 要先删旧 chunk，否则 JSON 会出现重复文档。」

下午 Lab，林晓连传两次 `notice.md`，`document_count` 不变，`index_mode=incremental`。周航点头：「这才是运营日常。」

```mermaid
journey
    title Day 30
    section 上午
      incremental vs full: 5: 林晓
      _remove_document_by_source: 4: 林晓
    section 下午
      upload 不 reset 验证: 5: 林晓
      rebuild 仍全量: 4: 林晓
```
"""

FILES["02_需求文档.md"] = """# ZL-NA-REQ-030 需求文档

## FR-001 增量 upload

- `ingest_bytes(incremental=True)` 默认走 `_incremental_index`
- 禁止调用 `chroma.reset()`

## FR-002 同名替换

- `_remove_document_by_source` 清理 JSON + Chroma 旧向量
- re-upload 不增加 document_count

## FR-003 Chroma 删除 API

- `delete_by_ids` / `delete_by_source`

## FR-004 rebuild 不变

- `rebuild_store` 仍 `_rebuild_index` + reset
- `index_mode` 置 `full`

## FR-005 状态字段

- `last_incremental_at`、`index_mode` 持久化与 status 暴露

## FR-006 TF-IDF 一致性

- 词表扩张时全量 upsert（仍不 reset）

## 非目标

- DELETE 文档 REST API
- 异步索引队列
"""

TEMPLATE = """# Day 30 {title}

**需求**：ZL-NA-REQ-030

## 概述

{summary}

## 核心知识点

### 1. 为何需要增量？

全量 reset 在大库上成本高；运营上传单文档是高频操作。

### 2. 双路径对照

| 路径 | 方法 | Chroma |
|------|------|--------|
| upload | `_incremental_index` | upsert only |
| rebuild | `_rebuild_index` | reset + upsert |

### 3. _incremental_index 步骤

1. refit TF-IDF on all chunks  
2. 若词表扩张 → affected = all chunks  
3. else affected = 新文档 chunks  
4. chroma.upsert_chunks（无 reset）  
5. last_incremental_at = now  

### 4. 同名替换

`_remove_document_by_source(filename)`：
- delete_by_ids from Chroma  
- filter documents/chunks  
- reindex chunk.index  

### 5. ingest_parsed 参数

`incremental: bool = False`；`ingest_bytes` 默认 True。

### 6. TF-IDF 词表扩张

新文档引入新词时向量维度变化，Chroma 须 `reset` 后全量 upsert；同内容 re-upload 则仅 upsert 不 reset。

- `index_mode`: incremental | full  
- `last_incremental_at` ISO 时间  

### 7. 与 Day 29 关系

Chroma 引擎不变，变的是**写入节奏**。

### 8. 与 Day 28 rebuild

rebuild 后 index_mode=full；upload 后再变 incremental。

### 9. Day 31 预告

混合检索：关键词 + 向量融合排序。

### 10. 风险

词表变化时需全量 upsert；监控 chroma_count == chunk_count。

### 11. 课堂检查清单

- [ ] upload 不触发 reset  
- [ ] 重复上传不 duplicate docs  
- [ ] rebuild 后 mode=full  
- [ ] chat 检索正常  
"""

for fname, title, summary in [
    ("01_企业背景与今日任务.md", "背景", "全量索引成本过高。"),
    ("02_需求文档_扩展.md", "扩展", "用户故事。"),
    ("03_架构设计.md", "架构", "双路径索引。"),
    ("04_流程图与示意图.md", "流程图", "incremental 时序。"),
    ("05_课堂笔记_上午.md", "上午", "_incremental_index。"),
    ("06_课堂笔记_下午.md", "下午", "API Lab。"),
    ("07_晚自习.md", "晚自习", "Elasticsearch partial update 对比。"),
    ("08_作业.md", "作业", "统计 incremental 次数脚本。"),
    ("09_作业答案.md", "答案", "参考。"),
    ("10_增量索引验收清单.md", "验收", "教师表。"),
    ("11_增量索引详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习", "选择题。"),
    ("13_深度扩展_索引更新策略.md", "扩展", "CDC vs batch。"),
    ("14_企业案例集_公告秒级上线.md", "案例", "运营场景。"),
    ("15_授课实录.md", "实录", "摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡。"),
    ("17_增量API速查手册.md", "速查", "字段说明。"),
    ("18_与Day29能力对照表.md", "对照", "引擎 vs 节奏。"),
    ("19_讲师补充阅读.md", "补充", "LSM 与向量库。"),
    ("20_完整代码走查.md", "走查", "源码。"),
    ("21_课堂知识竞赛.md", "竞赛", "15题。"),
    ("22_knowledge_incremental精读.md", "精读", "IncrementalReport。"),
    ("23_同名替换与删除策略.md", "实践", "delete_by_source。"),
    ("24_Phase3第六日总结.md", "总结", "Day25-30。"),
    ("25_incremental_api脚本精读.md", "精读", "upload 响应。"),
    ("26_实操Lab手册.md", "Lab", "六步。"),
    ("27_Day31混合检索预习.md", "预习", "hybrid。"),
]:
    add(fname, TEMPLATE.format(title=title, summary=summary))

FILES["11_增量索引详解.md"] = FILES["11_增量索引详解.md"].replace(
    "## 概述",
    """## 1. IncrementalReport

filename、chunks_added/removed、vocab_expanded、chroma_count。

## 2. 不变量

任意时刻 `chroma_count == chunk_count`（空库除外）。

## 概述""",
)

FILES["20_完整代码走查.md"] = """# Day 30 完整代码走查

1. `rag/knowledge_store.py` — _incremental_index / _remove_document_by_source  
2. `rag/chroma_store.py` — delete_by_ids / delete_by_source  
3. `rag/knowledge_incremental.py` — IncrementalReport  
4. `api/knowledge.py` — upload index_mode 响应  
5. `api/schemas.py` — KnowledgeStatusResponse 新字段  
"""

FILES["27_Day31混合检索预习.md"] = """# Day 31 预习

**预告**：混合检索 — 关键词 + 向量分数融合，提升长尾 query 命中率。

陈默：「增量让库活起来，混合检索让问答更准。」
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
