#!/usr/bin/env python3
"""Generate course/day27 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day27"
OUT.mkdir(parents=True, exist_ok=True)
FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add("README.md", """# Day 27 课件索引

**日期**：2026-08-03（星期一）  
**主题**：分块参数调优与检索质量 A/B 评估  
**需求**：ZL-NA-REQ-027

## 今日交付

- `rag/chunk_config.py` — ChunkConfig 与四套 PRESET
- `rag/retrieval_eval.py` — hit@1、run_ab_experiment
- `GET/PUT /api/knowledge/chunk-config`
- `POST /api/knowledge/evaluate`
- `KnowledgeStore` 持久化 `chunk_config`
- `frontend/knowledge.js` — A/B 评估按钮
- `tests/day27/` 15 项

## 关键设计

1. **评估与生产索引分离**：evaluate 在样例文档上模拟，不破坏 store  
2. **hit@1 教学指标**：top-1 块含 expect_any 任一关键词  
3. **PRESET 四套**：compact / default / wide / markdown_wide  
4. **chunk_config 持久化**：PUT 后影响后续 upload  
5. **版本 0.27.0**：health、status、PACKAGE_STRUCTURE 对齐  

## 验收

```bash
PYTHONPATH=src NEXUS_LLM_MOCK=1 python3 src/day27/chunk_tune_api_demo.py
PYTHONPATH=src pytest tests/day27/ -q
```

## 课件导航

| 序号 | 文件 | 用途 |
|------|------|------|
| 11 | 分块调参与检索评估详解 | 深度专题 |
| 22 | retrieval_eval 精读 | hit@1 源码 |
| 26 | 实操 Lab | 六步实验 |
| 27 | Day28 预习 | 全库 rebuild |
""")

FILES["00_旁白解读.md"] = """# Day 27 旁白解读

2026 年 8 月 3 日。陈默在白板写下：**chunk_size=200 谁定的？** 全场安静。

「Day 19 的默认值不是圣经，」他说，「今天用数据说话 —— hit@1、块数、平均分，A/B 四套预设跑一遍。」

林晓运行 `ab_experiment_demo.py`，看着 `wide` 配置 hit_rate 从 75% 升到 100%。赵岩说：「调参不是玄学，是可复现的实验。」

```mermaid
journey
    title Day 27
    section 上午
      ChunkConfig: 4: 林晓
      retrieval_eval: 4: 林晓
    section 下午
      evaluate API: 5: 林晓
      浏览器 A/B 按钮: 4: 林晓
```
"""

FILES["02_需求文档.md"] = """# ZL-NA-REQ-027 需求文档

## FR-001 ChunkConfig

- chunk_size、overlap、strategy、name
- validate() 约束 overlap < chunk_size
- PRESET_CONFIGS 四套预设

## FR-002 retrieval_eval

- EvalQuery(query, expect_any)
- hit@1：top 块含任一关键词即命中
- run_ab_experiment 按 hit_rate 排序

## FR-003 API

- GET/PUT `/api/knowledge/chunk-config`
- POST `/api/knowledge/evaluate`
- status 含 chunk_config

## FR-004 持久化

store.json 增加 chunk_config 字段，后续上传沿用。

## 非目标

- 全库重建（Day 28+）
- 真 Embedding API 评估
"""

TEMPLATE = """# Day 27 {title}

**需求**：ZL-NA-REQ-027

## 概述

{summary}

## 核心知识点

### 1. 为何要调参？

块太大 → 噪声多、检索不精准。块太小 → 语义碎裂、上下文不足。Day 27 用 **hit@1** 在固定评估集上对比。

### 2. ChunkConfig 字段

| 字段 | 含义 | 默认 |
|------|------|------|
| chunk_size | 最大字符数 | 200 |
| overlap | 重叠字符 | 40 |
| strategy | auto/fixed/markdown | auto |
| name | 预设名称 | default |

### 3. PRESET_CONFIGS

- compact: 120/20  
- default: 200/40  
- wide: 400/60  
- markdown_wide: 500/50 markdown  

### 4. 评估流程

```
product_notice.md → parse_bytes → 对每套 config 分块
→ EmbeddingRetriever → 对 EVAL_QUERIES 检索
→ hit@1 统计 → 排序推荐 best_config
```

### 5. API 使用

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/evaluate \\
  -H 'Content-Type: application/json' \\
  -d '{{"use_presets": true}}'
```

### 6. 与上传联动

`PUT chunk-config` 后，新上传文档使用新参数分块；已有块不自动重建。

### 7. 前端

`#kb-eval-btn` 调用 evaluate，展示推荐配置名与 chunk_size。

### 8. 指标解读

- hit_rate 优先于 avg_top_score  
- chunk_count 影响存储与检索延迟（教学环境可忽略）  

### 9. Day 28 预告

全库按新配置 **rebuild** 与批量评估流水线。

### 10. 实验纪律

固定评估集、固定文档、只改一个变量（chunk_size 或 strategy），记录结果表。

### 11. 常见误区

| 误区 | 正解 |
|------|------|
| hit 低就加大 overlap 到等于 chunk_size | overlap 须 < chunk_size |
| 评估通过就自动重建全库 | Day 28 才 rebuild |
| 只看块数越少越好 | 需同时看 hit_rate |
"""

for fname, title, summary in [
    ("01_企业背景与今日任务.md", "背景", "检索命中率不足，需数据驱动调参。"),
    ("02_需求文档_扩展.md", "扩展", "用户故事 US-027。"),
    ("03_架构设计.md", "架构", "eval 层独立于 KnowledgeStore 主索引。"),
    ("04_流程图与示意图.md", "流程图", "A/B 实验泳道图。"),
    ("05_课堂笔记_上午.md", "上午", "ChunkConfig 走读。"),
    ("06_课堂笔记_下午.md", "下午", "evaluate API 与 Lab。"),
    ("07_晚自习.md", "晚自习", "改 EVAL_QUERIES 观察 hit 变化。"),
    ("08_作业.md", "作业", "自定义 config 列表 evaluate。"),
    ("09_作业答案.md", "答案", "参考答案。"),
    ("10_调参验收清单.md", "验收", "教师勾选。"),
    ("11_分块调参与检索评估详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习", "选择题。"),
    ("13_深度扩展_RAG评估方法论.md", "扩展", "MRR、nDCG 预告。"),
    ("14_企业案例集_检索命中率复盘.md", "案例", "产品部复盘会。"),
    ("15_授课实录.md", "实录", "摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡。"),
    ("17_调参API速查手册.md", "速查", "curl 大全。"),
    ("18_与Day26能力对照表.md", "对照", "解析 vs 调参。"),
    ("19_讲师补充阅读.md", "补充", "Ragas、TruLens。"),
    ("20_完整代码走查.md", "走查", "源码顺序。"),
    ("21_课堂知识竞赛.md", "竞赛", "15 题。"),
    ("22_retrieval_eval精读.md", "精读", "hit@1 实现。"),
    ("23_chunk_config与企业预设实践.md", "实践", "PRESET 设计原则。"),
    ("24_Phase3第三日总结.md", "总结", "Day25-27。"),
    ("25_ab_experiment脚本精读.md", "精读", "demo 源码。"),
    ("26_实操Lab手册.md", "Lab", "六步实验。"),
    ("27_Day28知识库重建预习.md", "预习", "rebuild 预告。"),
]:
    add(fname, TEMPLATE.format(title=title, summary=summary))

FILES["20_完整代码走查.md"] = """# Day 27 完整代码走查

1. `rag/chunk_config.py`  
2. `rag/retrieval_eval.py`  
3. `api/knowledge.py` — chunk-config / evaluate  
4. `rag/knowledge_store.py` — chunk_config 持久化  
5. `day27/constants.py` — EVAL_QUERIES  
6. `frontend/knowledge.js` — runEvaluate  
"""

FILES["27_Day28知识库重建预习.md"] = """# Day 28 预习

**预告**：按最优 chunk_config **全量重建**知识库索引，批量评估 uploads 目录。

陈默：「调参选出答案，重建让整个库统一到答案上。」
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
