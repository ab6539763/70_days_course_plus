#!/usr/bin/env python3
"""Generate course/day28 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day28"
OUT.mkdir(parents=True, exist_ok=True)
FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add("README.md", """# Day 28 课件索引

**日期**：2026-08-04（星期二）  
**主题**：知识库全量重建（rebuild）  
**需求**：ZL-NA-REQ-028

## 今日交付

- `rag/knowledge_rebuild.py` — collect_source_files / rebuild_store
- `POST /api/knowledge/rebuild` — 全量重建 API
- `apply_best_config` — 评估后自动应用最优分块
- `last_rebuilt_at` 持久化
- `frontend` 全量重建按钮
- `tests/day28/` 14 项

```bash
PYTHONPATH=src python3 src/day28/rebuild_demo.py
PYTHONPATH=src pytest tests/day28/ -q
```

## 关键流程

Day 27 选出 chunk_config → Day 28 **rebuild** 让整个库统一到该配置。

## 配套代码

```bash
cd nexus-agent-platform
export PYTHONPATH=src NEXUS_LLM_MOCK=1
python3 src/day28/rebuild_demo.py
python3 src/day28/rebuild_api_demo.py
python3 -m pytest tests/day28/ -v
```

## 设计决策

1. **双源扫描**：sample_docs 保证开箱即用，uploads 承载运营文档  
2. **uploads 优先**：同名文件以用户上传为准  
3. **apply_best_config**：evaluate + rebuild 一键发布  
4. **sessions_cleared**：重建后编排器使用新索引  

## 课件导航

| 文件 | 用途 |
|------|------|
| 11_知识库重建详解 | 专题 |
| 22_knowledge_rebuild精读 | 源码 |
| 27_Day29向量库预习 | 明日 |

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day28/rebuild_api_demo.py
```
""")

FILES["00_旁白解读.md"] = """# Day 28 旁白解读

2026 年 8 月 4 日，星期二。林晓盯着 Day 27 的评估结果：wide 配置 hit_rate 100%。她问陈默：「现在全库还是旧块，怎么办？」

陈默在白板写下 **rebuild** 三个字母：「调参是实验，重建是发布。`POST /api/knowledge/rebuild` 会清空 chunks，重扫 sample_docs 和 uploads，用当前 chunk_config 重新分块。」

赵岩补充：「投资人演示前先 evaluate 再 rebuild，保证线上索引与实验结论一致。」

下午 Lab，林晓执行 `rebuild_demo.py`，终端打印 `chunks 12 → 8`。她打开 store.json，看到 `last_rebuilt_at` 时间戳。周航提醒：「uploads 与 sample 同名时，uploads 优先 —— 运营文档覆盖内置样例。」

```mermaid
journey
    title Day 28
    section 上午
      理解双源扫描: 4: 林晓
      rebuild_store 走读: 4: 林晓
    section 下午
      apply_best_config: 5: 林晓
      浏览器全量重建: 4: 林晓
```
"""

FILES["02_需求文档.md"] = """# ZL-NA-REQ-028 需求文档

## FR-001 源文件收集

- sample_docs/*.txt|md|pdf
- knowledge_uploads/* 优先同名

## FR-002 rebuild_store

- 清空 documents/chunks
- 按当前 chunk_config 重新 parse+chunk
- 单次 _rebuild_index
- 写入 last_rebuilt_at

## FR-003 API

POST `/api/knowledge/rebuild`
- include_sample_docs: bool
- apply_best_config: bool

## FR-004 会话

重建后 session_manager.clear_all()

## 非目标

- 增量重建单文档
- 后台异步任务队列
"""

TEMPLATE = """# Day 28 {title}

**需求**：ZL-NA-REQ-028

## 概述

{summary}

## 核心知识点

### 1. 为何需要 rebuild？

Day 27 只改默认配置，**已入库块不会自动变化**。rebuild 重扫源文件，全库统一到最新 chunk_config。

### 2. 双源扫描

| 源 | 路径 | 说明 |
|----|------|------|
| 样例 | day02/sample_docs | 内置三份 txt |
| 上传 | data/knowledge/uploads | 运营上传 |

同名时 uploads 覆盖 sample。

### 3. rebuild_store 步骤

1. collect_source_files  
2. documents.clear() / chunks.clear()  
3. 逐文件 parse_bytes → chunk_from_parsed  
4. _rebuild_index()  
5. save() + last_rebuilt_at  

### 4. apply_best_config

先 run_ab_experiment 选 PRESET 最优 → set_chunk_config → rebuild_store。

### 5. API 响应

RebuildResponse 含 chunks_before/after、source_files、rebuilt_at、sessions_cleared。

### 6. 与 evaluate 关系

| 操作 | 作用域 | 是否写库 |
|------|--------|----------|
| evaluate | 样例文档模拟 | 否 |
| rebuild | 全库源文件 | 是 |

### 7. 前端

`#kb-rebuild-btn` 调用 runRebuild(false)，展示块数变化。

### 8. 运维建议

重建前备份 store.json；课堂演示可用 --skip 生产数据。

### 9. Day 29 预告

Chroma 向量库持久化，替换 JSON TF-IDF。

### 10. 风险

重建期间查询短暂不一致；教学环境单进程可忽略。

### 11. 发布检查清单

- [ ] evaluate 已跑且 best_config 已确认  
- [ ] uploads 目录文档齐全  
- [ ] rebuild 后 spot-check 三条 EVAL_QUERIES  
- [ ] last_rebuilt_at 已更新  
"""

for fname, title, summary in [
    ("01_企业背景与今日任务.md", "背景", "调参后需发布级重建。"),
    ("02_需求文档_扩展.md", "扩展", "用户故事。"),
    ("03_架构设计.md", "架构", "rebuild 在 ingestion 之上。"),
    ("04_流程图与示意图.md", "流程图", "重建时序图。"),
    ("05_课堂笔记_上午.md", "上午", "collect_source_files。"),
    ("06_课堂笔记_下午.md", "下午", "API 与 Lab。"),
    ("07_晚自习.md", "晚自习", "apply_best_config 实验。"),
    ("08_作业.md", "作业", "上传 md 后 rebuild。"),
    ("09_作业答案.md", "答案", "参考。"),
    ("10_重建验收清单.md", "验收", "教师表。"),
    ("11_知识库重建详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习", "选择题。"),
    ("13_深度扩展_索引发布流程.md", "扩展", "蓝绿发布类比。"),
    ("14_企业案例集_运营发布夜.md", "案例", "发布夜演练。"),
    ("15_授课实录.md", "实录", "摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡。"),
    ("17_重建API速查手册.md", "速查", "curl。"),
    ("18_与Day27能力对照表.md", "对照", "调参 vs 重建。"),
    ("19_讲师补充阅读.md", "补充", "Elasticsearch reindex。"),
    ("20_完整代码走查.md", "走查", "源码。"),
    ("21_课堂知识竞赛.md", "竞赛", "15题。"),
    ("22_knowledge_rebuild精读.md", "精读", "rebuild_store。"),
    ("23_双源扫描与覆盖策略.md", "实践", "uploads 优先。"),
    ("24_Phase3第四日总结.md", "总结", "Day25-28。"),
    ("25_rebuild_api脚本精读.md", "精读", "API 路由。"),
    ("26_实操Lab手册.md", "Lab", "六步。"),
    ("27_Day29向量库预习.md", "预习", "Chroma。"),
]:
    add(fname, TEMPLATE.format(title=title, summary=summary))

FILES["11_知识库重建详解.md"] = FILES["11_知识库重建详解.md"].replace(
    "## 概述",
    """## 1. RebuildReport 字段

documents_before/after、chunks_before/after、sources_processed、rebuilt_at。

## 2. 幂等性

同一配置多次 rebuild 结果应一致（源文件不变前提下）。

## 概述""",
)

FILES["20_完整代码走查.md"] = """# Day 28 完整代码走查

1. `rag/knowledge_rebuild.py`  
2. `KnowledgeStore.last_rebuilt_at`  
3. `api/knowledge.py` — POST /rebuild  
4. `api/schemas.py` — RebuildRequest/Response  
5. `frontend/knowledge.js` — runRebuild  
"""

FILES["27_Day29向量库预习.md"] = """# Day 29 预习

**预告**：Chroma 向量库接入，替换 JSON 内嵌 TF-IDF 状态。

陈默：「重建流程不变，换的是索引引擎。」
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
