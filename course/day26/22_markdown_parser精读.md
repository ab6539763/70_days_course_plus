# markdown_parser.py 精读

**文件**：`tools/parsers/markdown_parser.py`

## 完整源码

```python
"""
Markdown 结构解析 — 标题分段、去代码块

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import re

from tools.parsers.base import DocumentSection, ParsedDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def parse_markdown(data: bytes, filename: str) -> ParsedDocument:
    raw = data.decode("utf-8")
    stripped = _FENCE.sub("", raw)
    stripped = _INLINE_CODE.sub(r"\1", stripped)
    stripped = _LINK.sub(r"\1", stripped)
    stripped = _BOLD.sub(r"\1", stripped)

    sections: list[DocumentSection] = []
    title = filename.rsplit(".", 1)[0]
    current_title = title
    current_level = 0
    current_lines: list[str] = []
    idx = 0

    for line in stripped.splitlines():
        match = _HEADING.match(line)
        if match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(
                        DocumentSection(
                            title=current_title,
                            body=body,
                            level=current_level,
                            index=idx,
                        )
                    )
                    idx += 1
            level = len(match.group(1))
            current_title = match.group(2).strip()
            current_level = level
            if level == 1 and not sections:
                title = current_title
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(
                DocumentSection(
                    title=current_title,
                    body=body,
                    level=current_level,
                    index=idx,
                )
            )

    plain_parts = [f"## {s.title}\n{s.body}" for s in sections if s.body]
    plain_text = "\n\n".join(plain_parts) if plain_parts else stripped.strip()

    return ParsedDocument(
        filename=filename,
        format="markdown",
        plain_text=plain_text,
        title=title,
        sections=sections,
        metadata={"heading_count": len(sections)},
    )
```


## 逐段解读

**L13-17 正则**：`_HEADING` 多级标题；`_FENCE` 剥离代码块；`_INLINE_CODE` 去反引号；`_LINK` 留链接文字；`_BOLD` 去星号。

**L34-56 状态机**：遇标题 flush 上一节 body；记录 level 与 title。

**L70-71 plain_text**：用 `## title\nbody` 拼接，供 fixed 策略与检索。

**L73-80 返回**：`metadata.heading_count` 便于测试断言。

## 与测试对照

`test_markdown_strips_code_fence`：`secret()` 不在 plain_text。  
`test_parse_markdown_sections`：titles 含「风险」。

## 样例文档

```markdown
# 智链科技理财产品说明

## 产品概述

灵犀稳健理财产品，面向合格投资者。

## 收益率

年化收益率可达 **8%**，历史业绩不代表未来表现。

## 起购门槛

最低起购金额为 **1000 元**。

## 风险提示

投资有风险，入市需谨慎。请仔细阅读产品说明书。

## 赎回规则

T+1 工作日到账，节假日顺延。

```python
# 示例代码块应被剥离，不参与检索
print("demo")
```
```


精读完。

---

## 逐行注释表

| 行 | 说明 |
|----|------|
| 13 | `_HEADING` 捕获 ATX 标题 |
| 14 | `_FENCE` 剥离代码块 |
| 22 | 先 strip fence 再分段 |
| 34-56 | 标题触发 flush section |
| 70-71 | plain_text 拼接格式 |
| 79 | heading_count 元数据 |



---

## 附录：完整 markdown_parser

```python
"""
Markdown 结构解析 — 标题分段、去代码块

需求：ZL-NA-REQ-026
"""

from __future__ import annotations

import re

from tools.parsers.base import DocumentSection, ParsedDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def parse_markdown(data: bytes, filename: str) -> ParsedDocument:
    raw = data.decode("utf-8")
    stripped = _FENCE.sub("", raw)
    stripped = _INLINE_CODE.sub(r"\1", stripped)
    stripped = _LINK.sub(r"\1", stripped)
    stripped = _BOLD.sub(r"\1", stripped)

    sections: list[DocumentSection] = []
    title = filename.rsplit(".", 1)[0]
    current_title = title
    current_level = 0
    current_lines: list[str] = []
    idx = 0

    for line in stripped.splitlines():
        match = _HEADING.match(line)
        if match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(
                        DocumentSection(
                            title=current_title,
                            body=body,
                            level=current_level,
                            index=idx,
                        )
                    )
                    idx += 1
            level = len(match.group(1))
            current_title = match.group(2).strip()
            current_level = level
            if level == 1 and not sections:
                title = current_title
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(
                DocumentSection(
                    title=current_title,
                    body=body,
                    level=current_level,
                    index=idx,
                )
            )

    plain_parts = [f"## {s.title}\n{s.body}" for s in sections if s.body]
    plain_text = "\n\n".join(plain_parts) if plain_parts else stripped.strip()

    return ParsedDocument(
        filename=filename,
        format="markdown",
        plain_text=plain_text,
        title=title,
        sections=sections,
        metadata={"heading_count": len(sections)},
    )
```


---

## 行级索引

- L13: `_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)`
- L14: `_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)`
- L20: `def parse_markdown(data: bytes, filename: str) -> ParsedDocu`
- L22: `stripped = _FENCE.sub("", raw)`
- L35: `match = _HEADING.match(line)`

## 与 product_notice 样例

```markdown
# 智链科技理财产品说明

## 产品概述

灵犀稳健理财产品，面向合格投资者。

## 收益率

年化收益率可达 **8%**，历史业绩不代表未来表现。

## 起购门槛

最低起购金额为 **1000 元**。

## 风险提示

投资有风险，入市需谨慎。请仔细阅读产品说明书。

## 赎回规则

T+1 工作日到账，节假日顺延。

```python
# 示例代码块应被剥离，不参与检索
print("demo")
```
```


精读专节完。

---

## 正则深度导读

`_FENCE` 非贪婪匹配 fence。`_HEADING` 要求 `#` 后空格。状态机 flush 时 body 非空才 append section。与 product_notice 五章对应。长文完。

---

## 备忘专节（22_markdown_parser精读.md）

智链 Day26 课件 `22_markdown_parser精读.md` 独立备忘：解析在 tools，索引在 store。 小组 1 负责本节复盘。

<!-- vol4-24-memo -->

### 索引 24 专属注记

本节与 ZL-NA-REQ-026 第 7 条 FR 呼应。 实验记录编号 EXP-D26-24。 讲师批注：复现 `pytest tests/day26/` 第 8 条相关测试。


---

## 正则

_HEADING 为何 MULTILINE


## markdown_parser 行级清单（全文件）

- L1 `"""`
- L2 `Markdown 结构解析 — 标题分段、去代码块`
- L4 `需求：ZL-NA-REQ-026`
- L5 `"""`
- L7 `from __future__ import annotations`
- L9 `import re`
- L11 `from tools.parsers.base import DocumentSection, Pa`
- L13 `_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MUL`
- L14 `_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILIN`
- L15 `_INLINE_CODE = re.compile(r"`([^`]+)`")`
- L16 `_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")`
- L17 `_BOLD = re.compile(r"\*\*([^*]+)\*\*")`
- L20 `def parse_markdown(data: bytes, filename: str) -> `
- L21 `raw = data.decode("utf-8")`
- L22 `stripped = _FENCE.sub("", raw)`
- L23 `stripped = _INLINE_CODE.sub(r"\1", stripped)`
- L24 `stripped = _LINK.sub(r"\1", stripped)`
- L25 `stripped = _BOLD.sub(r"\1", stripped)`
- L27 `sections: list[DocumentSection] = []`
- L28 `title = filename.rsplit(".", 1)[0]`
- L29 `current_title = title`
- L30 `current_level = 0`
- L31 `current_lines: list[str] = []`
- L32 `idx = 0`
- L34 `for line in stripped.splitlines():`
- L35 `match = _HEADING.match(line)`
- L36 `if match:`
- L37 `if current_lines:`
- L38 `body = "\n".join(current_lines).strip()`
- L39 `if body:`
- L40 `sections.append(`
- L41 `DocumentSection(`
- L42 `title=current_title,`
- L43 `body=body,`
- L44 `level=current_level,`
- L45 `index=idx,`
- L46 `)`
- L47 `)`
- L48 `idx += 1`
- L49 `level = len(match.group(1))`

## 与 _FENCE 测试用例

输入含 ```py secret() ``` 的 md；断言 plain_text 无 secret 有 visible。

行级清单完。

---

## 叙事专节

精读课发放源码打印件，要求标出状态机 flush 点。

<!-- narrative-22_markdown_parser精读.md -->
