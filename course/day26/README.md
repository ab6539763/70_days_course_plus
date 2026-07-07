# Day 26 课件索引

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
