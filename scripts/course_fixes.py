"""Apply per-day content overrides after course build() — fix copy-paste residue."""

from __future__ import annotations

import re

from course_diagrams import file04


def apply_fixes(day: int, files: dict[str, str]) -> dict[str, str]:
    files = dict(files)
    if 31 <= day <= 37:
        files["04_流程图与示意图.md"] = file04(day)
    if day == 35:
        files.update(_day35_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day35()
        files["10_Expansion验收清单.md"] = _acceptance_day35()
    elif day == 36:
        files.update(_day36_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day36()
        files["10_Route验收清单.md"] = _acceptance_day36()
    elif day == 37:
        files.update(_day37_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day37()
    return files


def post_fix_content(day: int, name: str, content: str) -> str:
    """Fix wrong day numbers and stale terminology without shrinking files."""
    skip_header_fix = name.startswith("27_")
    if day == 35:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[36, 37])
        content = _fix_day35_terms(content, name)
    elif day == 36:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[37])
        content = _fix_day36_terms(content, name)
    elif day == 37:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[])
        content = _fix_day37_terms(content, name)
    elif 31 <= day <= 34:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[d for d in range(31, 38) if d != day])
    return content


def _fix_headers(content: str, day: int, wrong_days: list[int]) -> str:
    for wrong in wrong_days:
        if wrong == day:
            continue
        content = re.sub(
            rf"^# Day {wrong}\b",
            f"# Day {day}",
            content,
            flags=re.M,
        )
        # Phase summary titles: （Day 36）inside day35 file
        content = re.sub(
            rf"（Day {wrong}）",
            f"（Day {day}）",
            content,
        )
    return content


def _apply_subs(content: str, subs: list[tuple[str, str]]) -> str:
    for old, new in subs:
        content = content.replace(old, new)
    return content


def _fix_day35_terms(content: str, name: str) -> str:
    if name == "27_Day36预习.md":
        return content  # next-day preview — keep Day 36 wording
    subs = [
        ("22_citation_builder精读.md", "22_query_expander精读.md"),
        ("精读：citation_builder 与引用溯源管线", "精读：query_expander 与多查询扩展管线"),
        ("## 一、citation_builder.py 全文", "## 一、query_expander.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、query_expander 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、query_expander 全文嵌入"),
        ("| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |", "| 2 | `query_expander.py` | expand + merge |"),
        ("| 1 | `citation_config.py` | validate / defaults |", "| 1 | `expansion_config.py` | validate / defaults |"),
        ("## 9. 完整 citation_builder（走查用）", "## 9. 完整 query_expander（走查用）"),
        ("| 15–40 | citation_builder + rewrite |", "| 15–40 | query_expander + expanding_retriever |"),
        ("**Q enabled=False 还构造 citation_builder 吗？**", "**Q enabled=False 还构造 ExpandingRetriever 吗？**"),
        ("构造但不调用 rewrite。", "构造但不调用 expand。"),
        ("1. citation_builder.py", "1. query_expander.py"),
        ("python3 -c \"import rag.citation_builder; print('ok')\"", "python3 -c \"import rag.query_expander; print('ok')\""),
        ("@router.get(\"/route-config\"", "@router.get(\"/expansion-config\""),
        ("@router.put(\"/route-config\"", "@router.put(\"/expansion-config\""),
        ("RouteConfigResponse", "ExpansionConfigResponse"),
        ("RouteConfig", "ExpansionConfig"),
        ("route-config", "expansion-config"),
        ("route-preview", "expansion-preview"),
        ("route_demo.py", "expansion_demo.py"),
        ("route_api_demo.py", "expansion_api_demo.py"),
        ("day36/expansion_demo.py", "day35/expansion_demo.py"),
        ("day36/expansion_api_demo.py", "day35/expansion_api_demo.py"),
        ("Citation 验收清单", "Expansion 验收清单"),
        ("引用溯源详解", "多查询扩展详解"),
        ("citation_builder.merge_retrieval_results", "query_expander.expand"),
        ("test_merge_retrieval_results_from_results", "test_expand_produces_multiple_queries"),
        ("test_citation_preview_with_rewrite", "test_expansion_preview_returns_queries"),
        ("citation_builder 精读完", "query_expander 精读完"),
        ("Phase 3 · Day 35 · Citation", "Phase 3 · Day 35 · Expansion"),
        ("Phase 3 第十一日总结（Day 35）", "Phase 3 第十一日总结（Day 35）"),
        ("# 多查询扩展详解（Day 35 专题）", "# 多查询扩展详解（Day 35 专题）"),
        ("| Day 33 查询改写 | Day 35 多查询扩展 |", "| Day 34 引用溯源 | Day 35 多查询扩展 |"),
        ("| Day 33 查询改写 | Day 36 多查询扩展 |", "| Day 34 引用溯源 | Day 35 多查询扩展 |"),
        ("打开 citation_builder，Citation 有 rank", "打开 query_expander，ExpansionResult 有 queries"),
        ("「打开 context，找 search。先看 enabled：关了就 hybrid。开则 pool=max(20,top_k)。inner 召回，citation_builder 逐对 rewrite，截断 top_k。这就是 ZL-NA-REQ-032 的读取路径。」",
         "「打开 ExpandingRetriever，找 search。先看 enabled：关了就 inner。开则 QueryExpander 生成多 query，逐路 search 后 merge 去重。这就是 ZL-NA-REQ-035 的读取路径。」"),
        ("这就是 ZL-NA-REQ-035。」", "这就是 ZL-NA-REQ-035。」"),
        ("citation-preview API", "expansion-preview API"),
        ("chat 响应 expansion.queries + merged citations + rewrite", "chat 响应 expansion.queries + merged citations"),
        ("**34** | **Citation** | **{VER}**", "**35** | **Expansion** | **v0.35.0**"),
        ("Day 36：HyDE / 多查询扩展", "Day 36：自适应路由"),
        ("from rag.citation_builder import _bigram_overlap", "from rag.result_merger import merge_retrieval_results"),
    ]
    return _apply_subs(content, subs)


def _fix_day36_terms(content: str, name: str) -> str:
    if name == "27_Day37预习.md":
        return content
    subs = [
        ("22_citation_builder精读.md", "22_query_router精读.md"),
        ("精读：citation_builder 与引用溯源管线", "精读：query_router 与自适应路由管线"),
        ("## 一、citation_builder.py 全文", "## 一、query_router.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、query_router 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、query_router 全文嵌入"),
        ("| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |", "| 2 | `query_router.py` | route + intent |"),
        ("| 1 | `citation_config.py` | validate / defaults |", "| 1 | `route_config.py` | validate / defaults |"),
        ("## 9. 完整 citation_builder（走查用）", "## 9. 完整 query_router（走查用）"),
        ("| 15–40 | citation_builder + rewrite |", "| 15–40 | query_router + routing_retriever |"),
        ("**Q enabled=False 还构造 citation_builder 吗？**", "**Q enabled=False 还构造 RoutingRetriever 吗？**"),
        ("1. citation_builder.py", "1. query_router.py"),
        ("python3 -c \"import rag.citation_builder; print('ok')\"", "python3 -c \"import rag.query_router; print('ok')\""),
        ("expansion-config", "route-config"),
        ("expansion-preview", "route-preview"),
        ("ExpansionConfig", "RouteConfig"),
        ("ExpansionConfigResponse", "RouteConfigResponse"),
        ("expansion_demo.py", "route_demo.py"),
        ("expansion_api_demo.py", "route_api_demo.py"),
        ("QueryExpander", "QueryRouter"),
        ("ExpandingRetriever", "RoutingRetriever"),
        ("多查询扩展详解", "自适应路由详解"),
        ("Expansion 验收清单", "Route 验收清单"),
        ("citation_builder.RuleBasedQueryRouter.route", "query_router.QueryRouter.route"),
        ("test_RuleBasedQueryRouter.route_from_results", "test_query_router_classifies_intent"),
        ("Phase 3 · Day 36 · Citation", "Phase 3 · Day 36 · Route"),
        ("Phase 3 第十二日总结（Day 36）", "Phase 3 第十二日总结（Day 36）"),
        ("Day 37：HyDE / 自适应路由", "Day 37：Self-RAG 答案校验"),
        ("# 自适应路由详解（Day 37 专题）", "# 自适应路由详解（Day 36 专题）"),
        ("| Day 33 查询改写 | Day 37 自适应路由 |", "| Day 35 多查询扩展 | Day 36 自适应路由 |"),
        ("ZL-NA-REQ-035", "ZL-NA-REQ-036"),
        ("citation_builder 精读完", "query_router 精读完"),
        ("打开 citation_builder，Citation 有 rank", "打开 query_router，RouteDecision 有 intent"),
        ("from rag.citation_builder import _bigram_overlap", "from rag.query_router import classify_intent"),
        ("浏览 `rag/citation_builder.py` 的 `CitationBundle`", "浏览 `rag/answer_validator.py` 的 `ValidationResult`"),
        ("chat 响应附带结构化 `expansion.queries + merged citations`", "chat 响应附带结构化 `route.intent + expand/rewrite 开关`"),
    ]
    return _apply_subs(content, subs)


def _fix_day37_terms(content: str, name: str) -> str:
    if name == "27_Day38预习.md":
        return content
    subs = [
        ("Expansion 验收清单", "Validation 验收清单"),
        ("与 Day 33 能力对照表", "与 Day 36 能力对照表"),
        ("| Day 33 查询改写 | Day 37 自适应路由 |", "| Day 36 自适应路由 | Day 37 答案校验 |"),
        ("精读：citation_builder 与自适应路由管线", "精读：answer_validator 与 Self-RAG 校验管线"),
        ("22_citation_builder精读.md", "22_answer_validator精读.md"),
        ("# Day 37 架构设计 — 自适应路由层", "# Day 37 架构设计 — Self-RAG 答案校验层"),
        ("知识库自适应路由", "Self-RAG 答案校验"),
        ("QueryRouter", "AnswerValidator"),
        ("route-config", "validation-config"),
        ("route-preview", "validation-preview"),
        ("RoutingRetriever.search", "validate_answer"),
        ("route_demo.py", "validation_demo.py"),
        ("route_api_demo.py", "validation_api_demo.py"),
        ("ZL-NA-REQ-035", "ZL-NA-REQ-037"),
        ("ZL-NA-REQ-036", "ZL-NA-REQ-037"),
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
        ("| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |", "| 2 | `answer_validator.py` | validate + score |"),
        ("| 1 | `citation_config.py` | validate / defaults |", "| 1 | `validation_config.py` | validate / defaults |"),
        ("## 9. 完整 citation_builder（走查用）", "## 9. 完整 answer_validator（走查用）"),
        ("| 15–40 | citation_builder + rewrite |", "| 15–40 | answer_validator + validation_config |"),
        ("**Q enabled=False 还构造 citation_builder 吗？**", "**Q enabled=False 还构造 AnswerValidator 吗？**"),
        ("1. citation_builder.py", "1. answer_validator.py"),
        ("python3 -c \"import rag.citation_builder; print('ok')\"", "python3 -c \"import rag.answer_validator; print('ok')\""),
        ("RouteConfig", "ValidationConfig"),
        ("RouteConfigRequest", "ValidationConfigRequest"),
        ("RouteConfigResponse", "ValidationConfigResponse"),
        ("store.set_citation_config(RouteConfig", "store.set_validation_config(ValidationConfig"),
        ("store.set_citation_config(ValidationConfig", "store.set_validation_config(ValidationConfig"),
        ("AnswerValidator + RouteConfig", "AnswerValidator + ValidationConfig"),
        ("口语命中 瓶颈与自适应路由", "答非所问瓶颈与 Self-RAG"),
        ("**09:40–10:30** 第二节：RouteConfig", "**09:40–10:30** 第二节：ValidationConfig"),
        ("## 第二节：RouteConfig（50 min）", "## 第二节：ValidationConfig（50 min）"),
        ("## 二十二、自适应路由伪代码", "## 二十二、Self-RAG 校验伪代码"),
        ("route-config HTTP 方法", "validation-config HTTP 方法"),
        ("指出 route-config 两个路由 HTTP 方法", "指出 validation-config 两个路由 HTTP 方法"),
        ("citation_builder.RuleBasedAnswerValidator.route", "answer_validator.RuleBasedAnswerValidator.validate"),
        ("test_RuleBasedAnswerValidator.route_from_results", "test_rule_based_validator_passes_good_answer"),
        ("from rag.citation_config import RouteConfig", "from rag.validation_config import ValidationConfig"),
        ("from rag.citation_builder import _bigram_overlap", "from rag.answer_validator import _token_overlap"),
        ("RAGContextService + RouteConfig", "KnowledgeStore + ValidationConfig"),
        ("route-config 两个路由", "validation-config 两个路由"),
        ("RuleBasedQueryRouter.route", "RuleBasedAnswerValidator.validate"),
        ("打分函数？ → `rewrite`", "打分函数？ → `validate`"),
        ("7. route-config HTTP 方法", "7. validation-config HTTP 方法"),
        ("1. 改写器类名？ → `RuleBasedQueryRouter.route`", "1. 校验器类名？ → `RuleBasedAnswerValidator`"),
        ("测试总数？ → 18", "测试总数？ → 21"),
        ("test_RuleBasedQueryRouter.route_from_results_candidates", "test_validator_rejects_off_topic_answer"),
        ("test_knowledge_store_persists_citation_config", "test_knowledge_store_persists_validation_config"),
    ]
    return _apply_subs(content, subs)


def _day35_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day35_file01(),
        "24_Phase3第十一日总结.md": _day35_file24(),
        "27_Day36预习.md": _day35_file27(),
        "18_与Day34能力对照表.md": _day35_file18(),
    }


def _day36_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day36_file01(),
        "24_Phase3第十二日总结.md": _day36_file24(),
        "27_Day37预习.md": _day36_file27(),
        "18_与Day35能力对照表.md": _day36_file18(),
    }


def _day37_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day37_file01(),
        "10_Validation验收清单.md": _acceptance_day37(),
        "11_答案校验详解.md": _day37_file11(),
        "18_与Day36能力对照表.md": _day37_file18(),
        "17_Validation_API速查手册.md": _day37_api_cheatsheet(),
    }


def _day35_file01() -> str:
    return """# Day 35 企业背景与今日任务

**需求**：ZL-NA-REQ-035 | **版本**：v0.35.0

## 背景

宽召回场景下单一 query 漏检率高。今日交付 **QueryExpander**、**expansion-config API** 与 **chat expansion** 字段。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | ExpansionConfig + RuleBasedQueryExpander |
| 下午 | Lab：expansion-preview + 多 query 截图 |
| 晚自习 | 读 Day 36 自适应路由预习 |

## 代码阅读顺序

1. `expansion_config.py`
2. `query_expander.py`
3. `expanding_retriever.py`
4. `result_merger.py`
5. `api/knowledge.py` expansion endpoints
6. `api/chat.py` expansion 字段
7. `tests/day35/`
"""


def _day35_file18() -> str:
    return """# Day 35 与 Day 34 能力对照表

| 维度 | Day 34 引用 | Day 35 扩展 |
|------|-------------|-------------|
| 阶段 | LLM 后展示 | 检索前扩展 |
| 配置 | CitationConfig | ExpansionConfig |
| API | citation-preview | expansion-preview |
| chat | citations[] | expansion.queries |
"""


def _day35_file24() -> str:
    return """# Phase 3 第十一日总结（Day 35）

## Day 35 交付物

- QueryExpander + ExpandingRetriever + ResultMerger
- expansion-config / expansion-preview API
- chat 响应 `expansion.queries` + merged citations
- tests/day35/ 20 项全绿
- 30 篇课件

## 核心能力

**宽召回**：一条问句变多条检索 query，merge 去重后进入 hybrid/rerank。

## 下一日

Day 36：自适应路由 — 按意图动态 expand/rewrite。
"""


def _day35_file27() -> str:
    return """# Day 36 预习：自适应路由与查询分类

**预告**：多 query 扩展提升了召回，但延迟随 query 数线性增长。Day 36 将引入 **Query Router** — 按意图决定是否 expand、rewrite 或直答 FAQ。

## 预习问

1. expand 与 rewrite 能否按 query 类型动态开关？
2. 路由误判如何降级回 Day 35 默认管线？

## Day 36 路线图（预期）

| 模块 | 说明 |
|------|------|
| query_router.py | 意图分类 + 管线分支 |
| RoutingRetriever | route → expand? → rewrite → hybrid |
"""


def _day36_file01() -> str:
    return """# Day 36 企业背景与今日任务

**需求**：ZL-NA-REQ-036 | **版本**：v0.36.0

## 背景

全量 expand 导致简单 FAQ 延迟过高。今日交付 **QueryRouter**、**route-config API** 与 **chat route** 字段。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | RouteConfig + RuleBasedQueryRouter |
| 下午 | Lab：route-preview + 快慢路径截图 |
| 晚自习 | 读 Day 37 Self-RAG 预习 |

## 代码阅读顺序

1. `route_config.py`
2. `query_router.py`
3. `routing_retriever.py`
4. `api/knowledge.py` route endpoints
5. `api/chat.py` route 字段
6. `tests/day36/`
"""


def _day36_file18() -> str:
    return """# Day 36 与 Day 35 能力对照表

| 维度 | Day 35 扩展 | Day 36 路由 |
|------|-------------|-------------|
| 阶段 | 检索前多 query | 检索前意图分流 |
| 配置 | ExpansionConfig | RouteConfig |
| API | expansion-preview | route-preview |
| chat | expansion | route |
"""


def _day36_file24() -> str:
    return """# Phase 3 第十二日总结（Day 36）

## Day 36 交付物

- QueryRouter + RoutingRetriever
- route-config / route-preview API
- chat 响应 `route.intent` + expand/rewrite 开关
- tests/day36/ 20 项全绿

## 核心能力

**自适应管线**：faq_fast 跳过 expand；rag_wide 走全链路。

## 下一日

Day 37：Self-RAG 答案校验 — LLM 后 citations 一致性校验。
"""


def _day36_file27() -> str:
    return """# Day 37 预习：Self-RAG 答案校验

**预告**：路由与检索已优化，但模型仍可能答非所问。Day 37 在 LLM 生成后用 citations 校验 reply。

## 预习问

1. 校验失败是否应拒答？
2. coverage 与 support_score 如何权衡？

## 预期模块

| 模块 | 说明 |
|------|------|
| answer_validator.py | RuleBasedAnswerValidator |
| validation-config API | 阈值与 refuse_on_fail |
"""


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
