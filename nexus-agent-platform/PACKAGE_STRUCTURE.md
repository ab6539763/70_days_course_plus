# NexusAgent 包结构说明

**版本**：v0.26.0（Day 26 文档解析）  
**需求**：ZL-NA-REQ-010 ~ ZL-NA-REQ-026

## Day 26 新增

```
src/tools/
  doc_parser.py           # 统一解析入口 parse_bytes
  parsers/
    markdown_parser.py    # Markdown 结构解析
    pdf_parser.py         # PDF 文本抽取 (pypdf)
    text_parser.py        # 纯文本
src/rag/
  chunk_strategies.py     # fixed vs markdown 分块对比
src/day26/
  sample_docs/            # product_notice.md / .pdf
  parse_demo.py
  chunk_compare_demo.py
```

## 支持上传格式

| 扩展名 | 解析器 | 默认分块 |
|--------|--------|----------|
| .txt | text_parser | fixed |
| .md | markdown_parser | markdown (auto) |
| .pdf | pdf_parser (pypdf) | fixed |

## API v0.26.0

- `POST /api/knowledge/upload` — 支持 .txt / .md / .pdf
- `GET /api/knowledge/status` — 含 `supported_formats`

## 依赖

```
pip install -r requirements-api.txt  # 含 pypdf
```
