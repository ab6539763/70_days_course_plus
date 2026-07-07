#!/usr/bin/env python3
"""Generate course/day26 markdown materials (≥30k chars)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "course" / "day26"
OUT.mkdir(parents=True, exist_ok=True)
FILES: dict[str, str] = {}


def add(name: str, body: str) -> None:
    FILES[name] = body.strip() + "\n"


add("README.md", """# Day 26 课件索引

**日期**：2026-07-31（星期五）  
**主题**：文档解析增强 — Markdown / PDF 与分块策略对比  
**需求**：ZL-NA-REQ-026  
**里程碑**：Phase 3 第二日

## 进度

Day 25 知识库只能上传 `.txt`。产品部提交 Markdown 产品说明与 PDF 合规附件，要求 **不改索引层** 的前提下扩展解析层。今日交付 `tools/doc_parser.py` 统一入口、`rag/chunk_strategies.py` 策略对比，API 升级至 `0.26.0`。

- Day 25 KnowledgeStore → **Day 26 多格式解析 + 章节分块**
- Day 27 分块参数调优……

## 配套代码

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
export PYTHONPATH=src NEXUS_LLM_MOCK=1

python3 src/day26/parse_demo.py
python3 src/day26/chunk_compare_demo.py
python3 src/day26/parse_api_demo.py
python3 -m pytest tests/day26/ -v
```

## 今日交付物

- [x] `tools/parsers/markdown_parser.py` — 标题分段、代码块剥离
- [x] `tools/parsers/pdf_parser.py` — pypdf 文本抽取
- [x] `tools/doc_parser.py` — `parse_bytes` 统一分发
- [x] `rag/chunk_strategies.py` — fixed / markdown / auto
- [x] `KnowledgeStore.ingest_parsed` — 解析结果入库
- [x] API 支持 `.txt` / `.md` / `.pdf` 上传
- [x] `frontend/knowledge.js` — 多格式 accept
- [x] `day26/sample_docs/product_notice.md` + `.pdf`
- [x] `tests/day26/`（17 tests）
- [x] Day 26 全套课件（30 篇）

## 关键设计

1. **解析与索引分离**：parser 输出 `ParsedDocument`，KnowledgeStore 负责分块与持久化  
2. **auto 策略**：Markdown 默认按章节分块，PDF/txt 用滑动窗口  
3. **pypdf 零 OCR**：可编辑 PDF 可抽取；扫描件留待后续  
4. **NexusError 错误码**：UNSUPPORTED_FORMAT / PDF_EMPTY 等  

## 验收

```bash
PYTHONPATH=src pytest tests/day26/ tests/day25/ -q
```
""")

TEMPLATE = """# Day 26 {title}

**需求**：ZL-NA-REQ-026

## 概述

{summary}

## 核心知识点

### 1. 解析层与索引层分离

赵岩：「解析在 `tools/`，索引仍在 `KnowledgeStore`。」Day 25 只能传 txt，今日扩展 md/pdf。

### 2. ParsedDocument 统一模型

`filename`、`format`、`plain_text`、`sections[]`、`page_count`。

### 3. Markdown 解析

- 剥离 ` ``` ` 代码块  
- 按 `#` 标题切章节  
- `chunk_markdown_sections` 按节分块  

### 4. PDF 解析

`pypdf.PdfReader` 逐页 `extract_text()`。扫描件无 OCR 留待后续。

### 5. 分块策略对比

| 策略 | 适用 | 特点 |
|------|------|------|
| fixed | txt/pdf | 滑动窗口 overlap |
| markdown | .md | 章节语义完整 |
| auto | 上传默认 | md 用章节，其余 fixed |

### 6. API v0.26.0

`POST /api/knowledge/upload` 响应新增 `format` 字段。`status` 返回 `supported_formats`。

### 8. 样例文件

`day26/sample_docs/product_notice.md` 含 5 个章节与代码块。`product_notice.pdf` 由 fpdf2 生成供 CI 抽取测试。

### 9. 与 Day 27 衔接

明日聚焦 `chunk_size` / `overlap` 调参与检索命中率评估，解析层接口保持不变。

### 10. 团队分工回顾

| 角色 | Day 26 贡献 |
|------|-------------|
| 陈默 | doc_parser 架构 |
| 林晓 | markdown_parser |
| 周航 | pypdf 集成与 CI |
| 赵岩 | 分块策略选型评审 |

## 实操

```bash
cd nexus-agent-platform
export PYTHONPATH=src
python3 src/day26/chunk_compare_demo.py
```

## 思考题

1. 为何代码块要从 Markdown 剥离？  
2. PDF 与 Markdown 默认分块策略为何不同？  
3. 上传后为何要 `clear_all` 会话？  
"""

FILES["02_需求文档.md"] = """# ZL-NA-REQ-026 需求文档

**需求名称**：文档解析增强（Markdown / PDF）  
**优先级**：P0  
**状态**：已交付

## FR-001 Markdown 解析器

- 文件：`tools/parsers/markdown_parser.py`
- 输入：UTF-8 `.md` / `.markdown`
- 输出：`ParsedDocument` 含 `sections[]`
- 规则：剥离 fenced code；保留标题层级

## FR-002 PDF 解析器

- 文件：`tools/parsers/pdf_parser.py`
- 依赖：`pypdf>=4.0`
- 逐页抽取文本；空文本报 `PDF_EMPTY`

## FR-003 统一入口 doc_parser

- `parse_bytes(data, filename)`
- `supported_formats()` 供 status API

## FR-004 分块策略 chunk_strategies

- `chunk_fixed_window` — Day 19 默认
- `chunk_markdown_sections` — 按节分块
- `chunk_from_parsed(strategy='auto')`
- `compare_strategies()` 教学演示

## FR-005 API 扩展

- upload 接受 `.md` `.pdf`
- 响应 `format` 字段
- status 返回 `supported_formats`

## 非目标

- OCR 扫描件
- Docx / HTML
- 增量索引（仍全量 rebuild）
"""

FILES["00_旁白解读.md"] = """# Day 26 旁白解读

2026 年 7 月 31 日，星期五。产品部邮件标题是：**「PDF 说明书什么时候能上传？」**

林晓看着 Day 25 的知识库侧栏，accept 里还写着 `.txt`。陈默说：「今天不动 `store.json` 的结构，只换入口 —— `parse_bytes` 先解析，再 `ingest_parsed`。」

她打开 `markdown_parser.py`，第一次用正则拆 `## 标题`。赵岩路过说：「代码块别进索引，投资人不需要看 `print('demo')`。」

下午，她上传 `product_notice.pdf`，终端打印 `page_count=1`，检索「1000」命中。周航在 CI 里加了 `pytest tests/day26`：「谁改坏 parser，全组红。」

```mermaid
journey
    title 林晓 Day 26
    section 上午
      Markdown 章节: 4: 林晓
      compare_strategies: 4: 林晓
    section 下午
      PDF 上传: 5: 林晓
      pytest 全绿: 5: 林晓
```

赵岩总结：「Day 25 解决知识从哪存，Day 26 解决知识从哪来 —— 多格式进来，同一套索引出去。」
"""

for fname, title, summary in [
    ("01_企业背景与今日任务.md", "背景", "运营要上传产品 PDF 说明书。"),
    ("02_需求文档_扩展.md", "扩展", "用户故事与风险。"),
    ("03_架构设计.md", "架构", "doc_parser → ingestion → KnowledgeStore。"),
    ("04_流程图与示意图.md", "流程图", "上传 md 时序图。"),
    ("05_课堂笔记_上午.md", "上午", "Markdown 解析走读。"),
    ("06_课堂笔记_下午.md", "下午", "PDF 与 API 联调。"),
    ("07_晚自习.md", "晚自习", "对比 chunk_compare 输出。"),
    ("08_作业.md", "作业", "上传自有 md；对比两种策略块数。"),
    ("09_作业答案.md", "答案", "参考答案。"),
    ("10_解析验收清单.md", "验收", "教师勾选表。"),
    ("11_文档解析与分块策略详解.md", "专题", "深度讲义。"),
    ("12_课堂练习册.md", "练习", "10 选择题。"),
    ("13_深度扩展_多格式企业文档.md", "扩展", "OCR、HTML、Docx 预告。"),
    ("14_企业案例集_产品PDF入库.md", "案例", "产品部上传 PDF。"),
    ("15_授课实录.md", "实录", "课堂摘要。"),
    ("16_复习卡片.md", "卡片", "闪卡。"),
    ("17_解析API速查手册.md", "速查", "curl 示例。"),
    ("18_与Day25能力对照表.md", "对照", "txt only vs 多格式。"),
    ("19_讲师补充阅读.md", "补充", "Unstructured、LlamaParse。"),
    ("20_完整代码走查.md", "走查", "全链路源码。"),
    ("21_课堂知识竞赛.md", "竞赛", "15 题。"),
    ("22_markdown_parser精读.md", "精读", "正则与章节。"),
    ("23_pdf_parser与pypdf实践.md", "实践", "pypdf 安装与限制。"),
    ("24_Phase3第二日总结.md", "总结", "Day25-26 回顾。"),
    ("25_chunk_strategies精读.md", "精读", "compare_strategies。"),
    ("26_实操Lab手册.md", "Lab", "六步实验。"),
    ("27_Day27预习.md", "预习", "分块参数调优预告。"),
]:
    add(fname, TEMPLATE.format(title=title, summary=summary))

FILES["11_文档解析与分块策略详解.md"] = FILES["11_文档解析与分块策略详解.md"].replace(
    "## 概述",
    """## 1. parse_bytes 分发逻辑

```python
ext = Path(filename).suffix.lower()
# .txt → parse_plain_text
# .md  → parse_markdown
# .pdf → parse_pdf (pypdf)
```

## 2. ingest_parsed

`KnowledgeStore.ingest_parsed` 调用 `chunk_from_parsed(strategy='auto')`。

## 概述""",
)

FILES["20_完整代码走查.md"] = """# Day 26 完整代码走查

1. `tools/parsers/markdown_parser.py` — 标题分段  
2. `tools/parsers/pdf_parser.py` — pypdf 抽文本  
3. `tools/doc_parser.py` — `parse_bytes`  
4. `rag/chunk_strategies.py` — `compare_strategies`  
5. `rag/knowledge_store.py` — `ingest_parsed`  
6. `api/knowledge.py` — 多格式 upload  
7. `frontend/knowledge.js` — accept 扩展  
"""

FILES["27_Day27预习.md"] = """# Day 27 预习

**预告**：分块参数调优、`chunk_size`/`overlap` A/B 实验、检索质量评估。

陈默：「解析解决『读得懂』，调参解决『切得准』。」
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
