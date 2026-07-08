"""Apply per-day content overrides after course build() — fix copy-paste residue."""

from __future__ import annotations

import re

from course_diagrams import file04


def apply_fixes(day: int, files: dict[str, str]) -> dict[str, str]:
    files = dict(files)
    if 31 <= day <= 37:
        files["04_流程图与示意图.md"] = file04(day)
    if day == 35:
        files["03_架构设计.md"] = _architecture_day35()
        files["10_Expansion验收清单.md"] = _acceptance_day35()
    elif day == 36:
        files["03_架构设计.md"] = _architecture_day36()
        files["10_Route验收清单.md"] = _acceptance_day36()
    elif day == 37:
        files.update(_day37_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day37()
    return files


def post_fix_content(day: int, name: str, content: str) -> str:
    """Fix wrong day numbers and stale terminology without shrinking files."""
    if day == 35:
        content = _fix_headers(content, day, wrong_days=[36])
        content = content.replace("Day 36 ", "Day 35 ")
    elif day == 36:
        content = _fix_headers(content, day, wrong_days=[37])
        content = content.replace("Day 37 ", "Day 36 ")
    elif day == 37:
        content = _fix_headers(content, day, wrong_days=[])
        content = _fix_day37_terms(content, name)
    elif 31 <= day <= 34:
        content = _fix_headers(content, day, wrong_days=[d for d in range(31, 38) if d != day])
    return content


def _fix_headers(content: str, day: int, wrong_days: list[int]) -> str:
    for wrong in wrong_days:
        if wrong == day:
            continue
        # Fix markdown H1 only when it says wrong day
        content = re.sub(
            rf"^# Day {wrong}\b",
            f"# Day {day}",
            content,
            flags=re.M,
        )
    return content


def _fix_day37_terms(content: str, name: str) -> str:
    """Replace stale route/citation wording in day37 body text."""
    if name == "27_Day38预习.md":
        return content
    subs = [
        ("Expansion 验收清单", "Validation 验收清单"),
        ("与 Day 33 能力对照表", "与 Day 36 能力对照表"),
        ("| Day 33 查询改写 | Day 37 自适应路由 |", "| Day 36 自适应路由 | Day 37 答案校验 |"),
        ("精读：citation_builder 与自适应路由管线", "精读：answer_validator 与 Self-RAG 校验管线"),
        ("# Day 37 架构设计 — 自适应路由层", "# Day 37 架构设计 — Self-RAG 答案校验层"),
        ("知识库自适应路由", "Self-RAG 答案校验"),
        ("QueryRouter", "AnswerValidator"),
        ("route-config", "validation-config"),
        ("route-preview", "validation-preview"),
        ("RoutingRetriever.search", "validate_answer"),
        ("route_demo.py", "validation_demo.py"),
        ("route_api_demo.py", "validation_api_demo.py"),
        ("ZL-NA-REQ-035", "ZL-NA-REQ-037"),
        ("include_route_meta", "refuse_on_fail"),
        ("expansion.queries + merged citations", "validation passed score reason"),
        ("HyDE 多查询预习", "多轮 Self-RAG 预习"),
        ("HyDE / 自适应路由", "Self-RAG 答案校验"),
        ("citation_builder 与自适应路由", "answer_validator 与 Self-RAG"),
        ("17_Route_API速查手册", "17_Validation_API速查手册"),
        ("意图路由与延迟方法论", "Self-RAG与幻觉率方法论"),
        ("快慢路径场景", "答非所问场景"),
        ("路由决策与SLA实践", "校验阈值与拒答实践"),
        ("自适应路由详解", "答案校验详解"),
        ("自适应路由专项验收", "答案校验专项验收"),
        ("自适应路由分层", "答案校验分层"),
        ("自适应路由方法论", "Self-RAG 与幻觉率方法论"),
        ("Day36 主题？ → query rewrite（自适应路由）", "Day37 主题？ → Self-RAG 答案校验"),
        ("下一日？ HyDE 自适应路由", "下一日？ 多轮 Self-RAG 重检索"),
        ("Phase 3 · Day 37 · Citation", "Phase 3 · Day 37 · Validation"),
        ("citation_builder 精读完", "answer_validator 精读完"),
        ("## 一、citation_builder.py 全文", "## 一、answer_validator.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、answer_validator 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、answer_validator 全文嵌入"),
        ("打开 citation_builder，Citation 有 rank", "打开 answer_validator，ValidationResult 有 passed"),
    ]
    for old, new in subs:
        content = content.replace(old, new)
    return content


def _day37_minimal_overrides() -> dict[str, str]:
    """Only replace files that must be short and correct; keep long walkthrough files."""
    return {
        "01_企业背景与今日任务.md": _day37_file01(),
        "10_Validation验收清单.md": _acceptance_day37(),
        "11_答案校验详解.md": _day37_file11(),
        "18_与Day36能力对照表.md": _day37_file18(),
        "17_Validation_API速查手册.md": _day37_api_cheatsheet(),
    }


def _day37_file01() -> str:
    return """# Day 37 企业背景与今日任务

**需求**：ZL-NA-REQ-037 | **版本**：v0.37.0

## 背景

合规审计：citations 已上线，但 **答非所问** 仍占 8%。今日交付 **AnswerValidator**、**validation-config API** 与 **chat validation** 字段。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | ValidationConfig + RuleBasedAnswerValidator |
| 下午 | Lab：validation-preview + 拒答截图 |
| 晚自习 | 读 Day 38 多轮 Self-RAG 预习 |

## 代码阅读顺序

1. `validation_config.py`  
2. `answer_validator.py`  
3. `knowledge_store.validate_answer`  
4. `api/knowledge.py` validation endpoints  
5. `api/chat.py` post-LLM validate  
6. `tests/day37/`  
"""


def _day37_file11() -> str:
    return """# 答案校验详解（Day 37 专题）

## 1. 校验时机

```
LLM 生成 reply → fetch citations → validate → 返回用户
```

## 2. 评分

- citation_coverage：引用被 reply 支撑的比例  
- support_score：reply token 与 citation 重叠度  
- strict 模式额外要求 coverage ≥ 50%

## 3. 拒答

`refuse_on_fail=true` → `[校验未通过]` + 安全话术

## 4. 与 route 正交

route 在检索前；validate 在 LLM 后。
"""


def _day37_file18() -> str:
    return """# Day 37 与 Day 36 能力对照表

| 维度 | Day 36 路由 | Day 37 校验 |
|------|-------------|-------------|
| 阶段 | 检索前 | LLM 后 |
| 配置 | RouteConfig | ValidationConfig |
| API | route-preview | validation-preview |
| chat | route | validation |
"""


def _day37_api_cheatsheet() -> str:
    return """# Validation API 速查手册

| 方法 | 路径 |
|------|------|
| GET | `/api/knowledge/validation-config` |
| PUT | `/api/knowledge/validation-config` |
| POST | `/api/knowledge/validation-preview` |
| POST | `/api/chat` → `validation` 字段 |
"""


def _architecture_day35() -> str:
    return """# Day 35 架构设计 — 多查询扩展层

## 1. 扩展分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> RAG[RAGContextService]
    RAG --> EXP[ExpandingRetriever]
    EXP --> X[QueryExpander]
    EXP --> INN[RewritingRetriever]
    CFG[ExpansionConfig] --> EXP
```

## 2. 组件

| 组件 | 职责 |
|------|------|
| query_expander.py | 单 query → 多 query |
| expanding_retriever.py | 多路 search + merge |
| result_merger.py | chunk_id 去重 |
"""


def _architecture_day36() -> str:
    return """# Day 36 架构设计 — 自适应路由层

## 1. 路由分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> RAG[RAGContextService]
    RAG --> RT[RoutingRetriever]
    RT --> QR[QueryRouter]
    RT --> EXP[ExpandingRetriever]
    CFG[RouteConfig] --> RT
```

## 2. intent 表

| intent | expand | rewrite |
|--------|--------|---------|
| faq_fast | off | off |
| rag_standard | off | on |
| rag_wide | on | on |
"""


def _architecture_day37() -> str:
    return """# Day 37 架构设计 — Self-RAG 答案校验层

## 1. 校验分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> ORCH[Orchestrator]
    ORCH --> REPLY[reply]
    CHAT --> CITE[fetch_citations]
    CITE --> VAL[AnswerValidator]
    REPLY --> VAL
    VAL --> OUT["validation meta"]
    CFG[ValidationConfig] --> VAL
```
"""


def _acceptance_day35() -> str:
    return """# Day 35 Expansion 验收清单

- [ ] expansion_demo / expansion-preview 绿  
- [ ] chat 含 expansion 字段  
- [ ] tests/day35/ 20 项全绿  
"""


def _acceptance_day36() -> str:
    return """# Day 36 Route 验收清单

- [ ] route_demo / route-preview 绿  
- [ ] chat 含 route 字段  
- [ ] tests/day36/ 20 项全绿  
"""


def _acceptance_day37() -> str:
    return """# Day 37 Validation 验收清单

- [ ] validation_demo / validation-preview 绿  
- [ ] chat 含 validation 字段  
- [ ] test_chat_refuses_on_fail 绿  
- [ ] tests/day37/ 21 项全绿  
"""
