# pdf_parser 与 pypdf 实践

## 完整源码

```python
"""
PDF 文本抽取 — 基于 pypdf

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import io

from core.exceptions import NexusError, StorageError
from tools.parsers.base import DocumentSection, ParsedDocument


def parse_pdf(data: bytes, filename: str) -> ParsedDocument:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise NexusError(
            "PDF 解析需要安装 pypdf：pip install pypdf",
            code="PDF_DEPS_MISSING",
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise NexusError(f"无法解析 PDF: {filename}", code="PDF_PARSE_ERROR") from exc

    pages: list[str] = []
    sections: list[DocumentSection] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        pages.append(text)
        if text:
            sections.append(
                DocumentSection(
                    title=f"第{i + 1}页",
                    body=text,
                    level=0,
                    index=i,
                )
            )

    plain_text = "\n\n".join(p for p in pages if p).strip()
    if not plain_text:
        raise NexusError(f"PDF 未提取到文本: {filename}", code="PDF_EMPTY")

    title = filename.rsplit(".", 1)[0]
    return ParsedDocument(
        filename=filename,
        format="pdf",
        plain_text=plain_text,
        title=title,
        sections=sections,
        page_count=len(reader.pages),
        metadata={"extractor": "pypdf"},
    )
```


## 实践步骤

```bash
pip install pypdf
python3 -c "
from pathlib import Path
from tools.doc_parser import parse_bytes
p = Path('src/day26/sample_docs/product_notice.pdf')
if p.is_file():
    d = parse_bytes(p.read_bytes(), p.name)
    print(d.page_count, '1000' in d.plain_text)
"
```

## 错误实验

`parse_bytes(b'%PDF broken', 'x.pdf')` → NexusError PDF_PARSE_ERROR

## 扫描件

无 OCR 时 `extract_text()` 空 → PDF_EMPTY。

实践完。

---

## pypdf 深入：页对象与 extract_text

`PdfReader.pages[i].extract_text()` 可能返回 None，代码 `or ""` 处理。多栏 PDF 可能乱序——生产用 pdfplumber。

## 与 test_parse_pdf_sample

样例路径 `day26/sample_docs/product_notice.pdf`；缺失时 skip 非 fail。CI 应用 fpdf2 从 md 文本生成。

## 扫描件教学脚本

讲师口述：「手机拍照 PDF 多半 PDF_EMPTY，不是你们代码写错。」

实践长文完。


---

## pypdf 安装与 CI

```bash
pip install pypdf fpdf2  # fpdf2 生成样例 pdf
```

## 页级 sections

pdf_parser 每页 `DocumentSection(title=f"第{i}页")`——fixed 策略仍用 plain_text 全文。

## 完整 pdf_parser 二次

```python
"""
PDF 文本抽取 — 基于 pypdf

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import io

from core.exceptions import NexusError, StorageError
from tools.parsers.base import DocumentSection, ParsedDocument


def parse_pdf(data: bytes, filename: str) -> ParsedDocument:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise NexusError(
            "PDF 解析需要安装 pypdf：pip install pypdf",
            code="PDF_DEPS_MISSING",
        ) from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise NexusError(f"无法解析 PDF: {filename}", code="PDF_PARSE_ERROR") from exc

    pages: list[str] = []
    sections: list[DocumentSection] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        pages.append(text)
        if text:
            sections.append(
                DocumentSection(
                    title=f"第{i + 1}页",
                    body=text,
                    level=0,
                    index=i,
                )
            )

    plain_text = "\n\n".join(p for p in pages if p).strip()
    if not plain_text:
        raise NexusError(f"PDF 未提取到文本: {filename}", code="PDF_EMPTY")

    title = filename.rsplit(".", 1)[0]
    return ParsedDocument(
        filename=filename,
        format="pdf",
        plain_text=plain_text,
        title=title,
        sections=sections,
        page_count=len(reader.pages),
        metadata={"extractor": "pypdf"},
    )
```


专节完。

---

## 生成

fpdf2 样例 pdf。

---

## 问答专节（23_pdf_parser与pypdf实践.md）

问：parse_bytes 作用？
答：扩展名分发 txt/md/pdf。

问：为何剥离代码块？
答：避免源码噪声进检索。

<!-- vol4-25-qa -->

### 索引 25 专属注记

本节与 ZL-NA-REQ-026 第 8 条 FR 呼应。 实验记录编号 EXP-D26-25。 讲师批注：复现 `pytest tests/day26/` 第 9 条相关测试。


---

## 表

| pdf | pages | 1000 |


---

## 叙事专节

实践课 USB 分发样例 pdf，解决三台机器 skip。

<!-- narrative-23_pdf_parser与pypdf实践.md -->
