# Day 26 课件索引

**日期**：2026-07-31（星期五）  
**主题**：文档解析增强 — Markdown / PDF 与分块策略对比  
**需求**：ZL-NA-REQ-026 | **版本**：0.26.0

## 进度

Day 25 知识库只能上传 `.txt`。产品提交 Markdown 产品说明与 PDF 合规附件。今日交付 `tools/doc_parser.py` 统一入口、`rag/chunk_strategies.py` 策略对比，API 升级至 `0.26.0`。

## 配套代码

```bash
cd nexus-agent-platform
pip install -r requirements-api.txt
pip install pypdf
export PYTHONPATH=src NEXUS_LLM_MOCK=1

python3 src/day26/parse_demo.py
python3 src/day26/chunk_compare_demo.py
python3 src/day26/parse_api_demo.py
python3 -m pytest tests/day26/ -v
```

## 交付物

- [x] `tools/parsers/markdown_parser.py` — 标题分段、代码块剥离
- [x] `tools/parsers/pdf_parser.py` — pypdf 文本抽取
- [x] `tools/doc_parser.py` — `parse_bytes` 统一分发
- [x] `rag/chunk_strategies.py` — fixed / markdown / auto
- [x] `KnowledgeStore.ingest_parsed` — 解析结果入库
- [x] API 支持 `.txt` / `.md` / `.pdf`
- [x] `tests/day26/` — 17 项
- [x] 全套课件 30 篇

## 导航

| 文件 | 用途 |
|------|------|
| 02 | 完整 PRD |
| 11 | 解析与分块详解 |
| 20 | 代码走查 + 时序图 |
| 22 | markdown_parser 精读 |
| 25 | chunk_strategies 精读 |
| 26 | Lab 手册 |

验收：`PYTHONPATH=src pytest tests/day26/ tests/day25/ -q`


---

## README 附录

验收：`pytest tests/day26/ -q` 期望 17 passed。样例：`product_notice.md` / `.pdf`。

---

## 附录

关键测试：`test_markdown_strips_code_fence`, `test_upload_pdf`, `test_chunk_markdown_auto_strategy`。

---

## 导读

关键词 parse_bytes、ParsedDocument、auto。验收 17 tests。

---

## 问答专节（README.md）

问：parse_bytes 作用？
答：扩展名分发 txt/md/pdf。

问：为何剥离代码块？
答：避免源码噪声进检索。

<!-- vol4-0-qa -->

### 索引 0 专属注记

本节与 ZL-NA-REQ-026 第 1 条 FR 呼应。 实验记录编号 EXP-D26-00。 讲师批注：复现 `pytest tests/day26/` 第 1 条相关测试。


---

## 索引补充

- parse_demo
- chunk_compare_demo
- pytest tests/day26


---

## 叙事专节

培训部把 Day26 README 第一行改成「先 compare 再 upload」，去年学员反向上传导致看不懂块数差异。

<!-- narrative-README.md -->
