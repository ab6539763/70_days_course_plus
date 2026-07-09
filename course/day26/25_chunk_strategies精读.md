# chunk_strategies.py 精读

## 完整源码

```python
"""
分块策略 — 固定窗口 vs Markdown 章节

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.chunker import TextChunk, chunk_text
from tools.parsers.base import DocumentSection, ParsedDocument


@dataclass
class ChunkStrategyResult:
    """策略对比结果"""

    strategy: str
    chunk_count: int
    chunks: list[TextChunk]
    preview: str


def chunk_fixed_window(
    text: str,
    *,
    source: str,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """Day 19 默认滑动窗口策略"""
    return chunk_text(text, chunk_size=chunk_size, overlap=overlap, source=source)


def chunk_markdown_sections(
    doc: ParsedDocument,
    *,
    max_chars: int = 400,
    overlap: int = 40,
) -> list[TextChunk]:
    """
    按 Markdown 章节分块：每节独立成块，过长再滑动切分。
    """
    if not doc.sections:
        return chunk_fixed_window(doc.plain_text, source=doc.filename)

    chunks: list[TextChunk] = []
    global_index = 0

    for section in doc.sections:
        header = f"[{section.title}] "
        body = section.body.strip()
        piece = f"{header}{body}" if body else section.title

        if len(piece) <= max_chars:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}",
                    text=piece,
                    source=doc.filename,
                    index=global_index,
                    start_char=0,
                    end_char=len(piece),
                )
            )
            global_index += 1
            continue

        sub_chunks = chunk_text(
            piece,
            chunk_size=max_chars,
            overlap=overlap,
            source=doc.filename,
        )
        for sub in sub_chunks:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}:{sub.index}",
                    text=sub.text,
                    source=doc.filename,
                    index=global_index,
                    start_char=sub.start_char,
                    end_char=sub.end_char,
                )
            )
            global_index += 1

    return chunks


def chunk_from_parsed(
    doc: ParsedDocument,
    *,
    strategy: str = "auto",
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """根据文档类型与策略选择分块方式"""
    chosen = strategy
    if strategy == "auto":
        chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"

    if chosen == "markdown":
        return chunk_markdown_sections(doc, max_chars=chunk_size, overlap=overlap)
    return chunk_fixed_window(
        doc.plain_text,
        source=doc.filename,
        chunk_size=chunk_size,
        overlap=overlap,
    )


def compare_strategies(doc: ParsedDocument) -> list[ChunkStrategyResult]:
    """对比固定窗口与章节策略（教学演示用）"""
    fixed = chunk_fixed_window(doc.plain_text, source=doc.filename)
    section = chunk_markdown_sections(doc) if doc.sections else fixed

    return [
        ChunkStrategyResult(
            strategy="fixed",
            chunk_count=len(fixed),
            chunks=fixed,
            preview=fixed[0].text[:80] if fixed else "",
        ),
        ChunkStrategyResult(
            strategy="markdown",
            chunk_count=len(section),
            chunks=section,
            preview=section[0].text[:80] if section else "",
        ),
    ]
```


## chunk_fixed_window

委托 Day 19 `chunk_text`，参数 chunk_size/overlap。

## chunk_markdown_sections

- 无 sections 回退 fixed  
- 每节前缀 `[title]`  
- 超长节再 `chunk_text`  

## chunk_from_parsed

```python
if strategy == "auto":
    chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"
```

## compare_strategies

教学用，返回 `ChunkStrategyResult` 含 preview 前 80 字符。

## ingest_parsed 衔接

```python
def validate_answer(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult | None:
        """按当前 validation_config 校验 reply 与 citations 一致性"""
        cfg = self.get_validation_config()
        if not cfg.enabled:
            return None
        validator = RuleBasedAnswerValidator(config=cfg)
        return validator.validate(query, reply, citations)

    def fetch_citations(self, query: str) -> dict[str, Any]:
        """按当前 citation_config 检索并返回引用包 dict"""
        cfg = self.get_citation_config()
        if not cfg.enabled:
            return {
                "query": query.strip(),
                "citations": [],
                "rewrite": None,
                "expansion": None,
                "route": None,
            }
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(query, config=cfg)
        return bundle.to_dict()

    def fetch_citations_retry(self, query: str, *, attempt: int = 1) -> dict[str, Any]:
```


精读完。

---

## 附录：KnowledgeStore.ingest_parsed 全文节选

```python
def validate_answer(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult | None:
        """按当前 validation_config 校验 reply 与 citations 一致性"""
        cfg = self.get_validation_config()
        if not cfg.enabled:
            return None
        validator = RuleBasedAnswerValidator(config=cfg)
        return validator.validate(query, reply, citations)

    def fetch_citations(self, query: str) -> dict[str, Any]:
        """按当前 citation_config 检索并返回引用包 dict"""
        cfg = self.get_citation_config()
        if not cfg.enabled:
            return {
                "query": query.strip(),
                "citations": [],
                "rewrite": None,
                "expansion": None,
                "route": None,
            }
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(query, config=cfg)
        return bundle.to_dict()

    def fetch_citations_retry(self, query: str, *, attempt: int = 1) -> dict[str, Any]:
        """Self-RAG 重试 — 强制 rag_wide 并放大 citation pool"""
        from rag.citation_config import CitationConfig
        from rag.route_config import INTENT_RAG_WIDE

        cfg = self.get_citation_config()
        if not cfg.enabled:
            return self.fetch_citations(query)

        boosted = CitationConfig.from_dict(
            {
                **cfg.to_dict(),
                "max_citations": min(100, max(cfg.max_citations, 20) + attempt * 10),
            }
        )
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(
            query,
            config=boosted,
            intent_override=INTENT_RAG_WIDE,
        )
        data = bundle.to_dict()
```


## 附录：compare_strategies 使用

```python
from tools.doc_parser import parse_bytes
from rag.chunk_strategies import compare_strategies
doc = parse_bytes(open("src/day26/sample_docs/product_notice.md","rb").read(), "p.md")
for r in compare_strategies(doc):
    print(r.strategy, r.chunk_count, r.preview)
```



---

## 附录：compare_strategies 演示

运行 `python3 src/day26/chunk_compare_demo.py`。

---

## 附录：chunk 全文二次导读

```python
"""
分块策略 — 固定窗口 vs Markdown 章节

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.chunker import TextChunk, chunk_text
from tools.parsers.base import DocumentSection, ParsedDocument


@dataclass
class ChunkStrategyResult:
    """策略对比结果"""

    strategy: str
    chunk_count: int
    chunks: list[TextChunk]
    preview: str


def chunk_fixed_window(
    text: str,
    *,
    source: str,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """Day 19 默认滑动窗口策略"""
    return chunk_text(text, chunk_size=chunk_size, overlap=overlap, source=source)


def chunk_markdown_sections(
    doc: ParsedDocument,
    *,
    max_chars: int = 400,
    overlap: int = 40,
) -> list[TextChunk]:
    """
    按 Markdown 章节分块：每节独立成块，过长再滑动切分。
    """
    if not doc.sections:
        return chunk_fixed_window(doc.plain_text, source=doc.filename)

    chunks: list[TextChunk] = []
    global_index = 0

    for section in doc.sections:
        header = f"[{section.title}] "
        body = section.body.strip()
        piece = f"{header}{body}" if body else section.title

        if len(piece) <= max_chars:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}",
                    text=piece,
                    source=doc.filename,
                    index=global_index,
                    start_char=0,
                    end_char=len(piece),
                )
            )
            global_index += 1
            continue

        sub_chunks = chunk_text(
            piece,
            chunk_size=max_chars,
            overlap=overlap,
            source=doc.filename,
        )
        for sub in sub_chunks:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}:{sub.index}",
                    text=sub.text,
                    source=doc.filename,
                    index=global_index,
                    start_char=sub.start_char,
                    end_char=sub.end_char,
                )
            )
            global_index += 1

    return chunks


def chunk_from_parsed(
    doc: ParsedDocument,
    *,
    strategy: str = "auto",
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """根据文档类型与策略选择分块方式"""
    chosen = strategy
    if strategy == "auto":
        chosen = "markdown" if doc.format == "markdown" and doc.sections else "fixed"

    if chosen == "markdown":
        return chunk_markdown_sections(doc, max_chars=chunk_size, overlap=overlap)
    return chunk_fixed_window(
        doc.plain_text,
        source=doc.filename,
        chunk_size=chunk_size,
        overlap=overlap,
    )


def compare_strategies(doc: ParsedDocument) -> list[ChunkStrategyResult]:
    """对比固定窗口与章节策略（教学演示用）"""
    fixed = chunk_fixed_window(doc.plain_text, source=doc.filename)
    section = chunk_markdown_sections(doc) if doc.sections else fixed

    return [
        ChunkStrategyResult(
            strategy="fixed",
            chunk_count=len(fixed),
            chunks=fixed,
            preview=fixed[0].text[:80] if fixed else "",
        ),
        ChunkStrategyResult(
            strategy="markdown",
            chunk_count=len(section),
            chunks=section,
            preview=section[0].text[:80] if section else "",
        ),
    ]
```


## 数学直觉

fixed：O(n) 滑动；markdown：O(sections) 优先语义边界。  
长 section 仍回退 chunk_text——无免费午餐。

## 实验记录模板

| strategy | count | 首块前缀 |
|----------|-------|----------|
| fixed | ? | ? |
| markdown | ? | [产品概述] |

专节完。

---

## 策略伪代码

auto 时 md+sections 用 markdown，否则 fixed。Day 27 evaluate 用 hit@1 量化。ChunkStrategyResult.preview 前 80 字符课堂对比。长文完。

---

## 案例专节（25_chunk_strategies精读.md）

运营传 product_notice.md，问「年化收益率」，应命中含 8% 的章节块。
若命中 fixed 碎块，Day27 evaluate 调参。

<!-- vol4-27-case -->

### 索引 27 专属注记

本节与 ZL-NA-REQ-026 第 1 条 FR 呼应。 实验记录编号 EXP-D26-27。 讲师批注：复现 `pytest tests/day26/` 第 11 条相关测试。


---

## id

markdown 块 id 含 :sec:


## chunk_strategies 二次精读：逐函数

### chunk_fixed_window

```python
def chunk_fixed_window(
    text: str,
    *,
    source: str,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """Day 19 默认滑动窗口策略"""
    return chunk_text(text, chunk_size=chunk_size, overlap=overlap, source=source)
```


委托 `chunk_text`，保持 Day 19 滑动窗口语义。

### chunk_markdown_sections 核心循环

```python
doc: ParsedDocument,
    *,
    max_chars: int = 400,
    overlap: int = 40,
) -> list[TextChunk]:
    """
    按 Markdown 章节分块：每节独立成块，过长再滑动切分。
    """
    if not doc.sections:
        return chunk_fixed_window(doc.plain_text, source=doc.filename)

    chunks: list[TextChunk] = []
    global_index = 0

    for section in doc.sections:
        header = f"[{section.title}] "
        body = section.body.strip()
        piece = f"{header}{body}" if body else section.title

        if len(piece) <= max_chars:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}",
                    text=piece,
                    source=doc.filename,
                    index=global_index,
                    start_char=0,
                    end_char=len(piece),
                )
            )
            global_index += 1
            continue

        sub_chunks = chunk_text(
            piece,
            chunk_size=max_chars,
            overlap=overlap,
            source=doc.filename,
        )
        for sub in sub_chunks:
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.filename}:sec:{section.index}:{sub.index}",
                    text=sub.text,
                    source=doc.filename,
                    index=global_index,
                    start_char=sub.start_char,
                    end_char=sub.end_char,
                )
            )
            global_index += 1

    return chunks
```


每节前缀 `[title]` 利于检索时显示章节语境。超长节 fallback `chunk_text` 避免单块超大。

### compare_strategies 教学输出

```python
"""对比固定窗口与章节策略（教学演示用）"""
    fixed = chunk_fixed_window(doc.plain_text, source=doc.filename)
    section = chunk_markdown_sections(doc) if doc.sections else fixed

    return [
        ChunkStrategyResult(
            strategy="fixed",
            chunk_count=len(fixed),
            chunks=fixed,
            preview=fixed[0].text[:80] if fixed else "",
        ),
        ChunkStrategyResult(
            strategy="markdown",
            chunk_count=len(section),
            chunks=section,
            preview=section[0].text[:80] if section else "",
        ),
    ]
```


课堂演示应打印 strategy、chunk_count、preview 三列。

### 与 test_chunk_markdown_auto_strategy

上传 product_notice 后 auto 至少 3 块，且任一块含「起购」或「1000」。

二次精读完。

---

## 叙事专节

compare 演示时 markdown 首块含 [产品概述] 前缀全场拍照。

<!-- narrative-25_chunk_strategies精读.md -->
