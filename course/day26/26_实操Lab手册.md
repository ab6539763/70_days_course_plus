# Day 26 实操 Lab

## Lab 0

```bash
pip install pypdf
export PYTHONPATH=src
pytest tests/day26/ -v
```

## Lab 1 parse_demo

```bash
python3 src/day26/parse_demo.py
```

## Lab 2 chunk_compare

```bash
python3 src/day26/chunk_compare_demo.py
```

记录 fixed vs markdown chunk_count。

## Lab 3 上传 md

Swagger 上传 product_notice.md，`format==markdown`。

## Lab 4 上传 pdf

上传 pdf，`format==pdf`，chat 问起购金额。

## Lab 5 代码块

上传含 code fence 的 md，检索不应命中 fence 内符号。

## Lab 6 策略实验

```python
from tools.doc_parser import parse_bytes
from rag.chunk_strategies import chunk_from_parsed
doc = parse_bytes(open("src/day26/sample_docs/product_notice.md","rb").read(), "p.md")
print(len(chunk_from_parsed(doc, strategy="fixed")))
print(len(chunk_from_parsed(doc, strategy="markdown")))
```

<details><summary>期望</summary>markdown 块数通常更少且语义完整</details>

---

## Lab 7–10 详解

**Lab 7** 上传 docx，记录 422 detail 全文。**Lab 8** 损坏 pdf 400。**Lab 9** strategy_report 表格。**Lab 10** 200 字结论：product_notice 适合 markdown 策略因五章标题清晰。

## 互评 Rubric

| 项 | 通过 |
|----|------|
| pytest 17 | 全绿 |
| md upload | format 对 |
| compare 输出 | 两行 |
| chat 命中 | 起购金额 |

Lab 详解完。


---

## Lab 7–9 加分

Lab 7：上传 .docx → 422 截图  
Lab 8：损坏 pdf → 400  
Lab 9：撰写 strategy_report.md  

## 互评

三人组交换 Lab 6 输出，核对 markdown 块含 `[` 标题前缀。

Lab 专节完。

---

## 安全

禁 PII pdf。

---

## 排错专节（26_实操Lab手册.md）

| 现象 | 处理 |
|------|------|
| PDF_EMPTY | 换可编辑 pdf |
| 422 docx | 仅 txt/md/pdf |
| chunk 过少 | 检查 auto 策略 |

<!-- vol4-28-debug -->

### 索引 28 专属注记

本节与 ZL-NA-REQ-026 第 2 条 FR 呼应。 实验记录编号 EXP-D26-28。 讲师批注：复现 `pytest tests/day26/` 第 12 条相关测试。


---

## Lab10

200 字 compare 结论


---

## 叙事专节

Lab 互评：strategy 结论须引用 chunk_count 数字。

<!-- narrative-26_实操Lab手册.md -->
