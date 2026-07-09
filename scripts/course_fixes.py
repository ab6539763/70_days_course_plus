"""Apply per-day content overrides after course build() — fix copy-paste residue."""

from __future__ import annotations

import re

from course_diagrams import file04


def apply_fixes(day: int, files: dict[str, str]) -> dict[str, str]:
    files = dict(files)
    if 31 <= day <= 41:
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
    elif day == 38:
        files.update(_day38_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day38()
    elif day == 39:
        files.update(_day39_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day39()
    elif day == 40:
        files.update(_day40_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day40()
    elif day == 41:
        files.update(_day41_minimal_overrides())
        files["03_架构设计.md"] = _architecture_day41()
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
    elif day == 38:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[37])
        content = _fix_day38_terms(content, name)
    elif day == 39:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[37, 38])
        content = _fix_day39_terms(content, name)
    elif day == 40:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[37, 38, 39])
        content = _fix_day40_terms(content, name)
    elif day == 41:
        if not skip_header_fix:
            content = _fix_headers(content, day, wrong_days=[37, 38, 39, 40])
        content = _fix_day41_terms(content, name)
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


def _fix_day38_terms(content: str, name: str) -> str:
    if name == "27_Day39预习.md":
        return content
    subs = [
        ("22_answer_validator精读.md", "22_validation_retry精读.md"),
        ("17_Validation_API速查手册", "17_Retry_API速查手册"),
        ("精读：answer_validator 与 Self-RAG 校验管线", "精读：validation_retry 与多轮 Self-RAG 重试管线"),
        ("## 一、answer_validator.py 全文", "## 一、validation_retry.py 全文"),
        ("## 二十一、answer_validator 完整源码", "## 二十一、validation_retry 完整源码"),
        ("## 四十、answer_validator 全文嵌入", "## 四十、validation_retry 全文嵌入"),
        ("| 2 | `answer_validator.py` | validate + score |", "| 2 | `validation_retry.py` | retry + rag_wide |"),
        ("| 1 | `validation_config.py` | validate / defaults |", "| 1 | `validation_config.py` | retry_on_fail / max_retries |"),
        ("## 9. 完整 answer_validator（走查用）", "## 9. 完整 validation_retry（走查用）"),
        ("| 15–40 | answer_validator + validation_config |", "| 15–40 | validation_retry + fetch_citations_retry |"),
        ("1. answer_validator.py", "1. validation_retry.py"),
        ("python3 -c \"import rag.answer_validator; print('ok')\"", "python3 -c \"import rag.validation_retry; print('ok')\""),
        ("答案校验详解", "校验重试详解"),
        ("Validation 验收清单", "Retry 验收清单"),
        ("与 Day 36 能力对照表", "与 Day 37 能力对照表"),
        ("| Day 36 自适应路由 | Day 37 答案校验 |", "| Day 37 答案校验 | Day 38 校验重试 |"),
        ("Phase 3 · Day 37 · Validation", "Phase 3 · Day 38 · Retry"),
        ("Phase 3 第十二日总结（Day 37）", "Phase 3 第十三日总结（Day 38）"),
        ("ZL-NA-REQ-037", "ZL-NA-REQ-038"),
        ("v0.37.0", "v0.38.0"),
        ("validation_demo.py", "retry_demo.py"),
        ("validation_api_demo.py", "retry_api_demo.py"),
        ("validate_answer", "apply_validation_retry"),
        ("Self-RAG 答案校验", "多轮 Self-RAG 校验重试"),
        ("答案校验分层", "校验重试分层"),
        ("校验阈值与拒答实践", "重试阈值与拒答实践"),
        ("答非所问场景", "校验失败恢复场景"),
        ("Self-RAG与幻觉率方法论", "多轮Self-RAG方法论"),
        ("Day37 主题？ → Self-RAG 答案校验", "Day38 主题？ → 校验失败重试"),
        ("tests/day37/", "tests/day38/"),
        ("day37/", "day38/"),
        ("21 项全绿", "15 项全绿"),
        ("RuleBasedAnswerValidator", "apply_validation_retry"),
        ("打开 answer_validator，ValidationResult 有 passed", "打开 validation_retry，ValidationRetryOutcome 有 retries"),
        ("citation_builder", "validation_retry"),
        ("route-config", "validation-config"),
        ("route-preview", "validation-retry-preview"),
        ("自适应路由", "校验重试"),
        ("AnswerValidator", "ValidationRetry"),
    ]
    return _apply_subs(content, subs)


def _day38_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day38_file01(),
        "10_Retry验收清单.md": _acceptance_day38(),
        "11_校验重试详解.md": _day38_file11(),
        "17_Retry_API速查手册.md": _day38_api_cheatsheet(),
        "18_与Day37能力对照表.md": _day38_file18(),
        "24_Phase3第十三日总结.md": _day38_file24(),
    }


def _day38_file01() -> str:
    return """# Day 38 企业背景与今日任务

**需求**：ZL-NA-REQ-038 | **版本**：v0.38.0

## 背景

Day 37 拒答降低了幻觉风险，但 **误拒** 与 **可恢复失败** 需二次机会。今日交付 **validation_retry**、**fetch_citations_retry** 与 **validation-retry-preview**。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | retry_on_fail + apply_validation_retry |
| 下午 | Lab：validation-retry-preview + retries 截图 |
| 晚自习 | 读 Day 39 Agent 工具链预习 |

## 代码阅读顺序

1. `validation_config.py` — retry_on_fail / max_retries
2. `validation_retry.py`
3. `knowledge_store.fetch_citations_retry`
4. `api/chat.py` retry 循环
5. `tests/day38/`
"""


def _day38_file11() -> str:
    return """# 校验重试详解（Day 38 专题）

## 1. 重试时机

```
validate 失败 → fetch_citations_retry(rag_wide) → 再 validate → 仍失败则拒答
```

## 2. 策略

- `retry_on_fail=true` 且 `max_retries>=1` 才重试
- 重试强制 `intent=rag_wide`，放大 citation pool
- `refuse_on_fail` 在重试耗尽后生效

## 3. 审计字段

`validation.retries`、`validation.retry_route`
"""


def _day38_file18() -> str:
    return """# Day 38 与 Day 37 能力对照表

| 维度 | Day 37 校验 | Day 38 重试 |
|------|-------------|-------------|
| 失败处理 | 直接拒答 | rag_wide 重检索后再校验 |
| 配置 | refuse_on_fail | + retry_on_fail / max_retries |
| API | validation-preview | + validation-retry-preview |
| chat | validation | + retries / retry_route |
"""


def _day38_file24() -> str:
    return """# Phase 3 第十三日总结（Day 38）

## Day 38 交付物

- validation_retry.py + fetch_citations_retry
- validation-retry-preview API
- chat retry 循环与 retries 审计
- tests/day38/ 15 项全绿

## 核心能力

**可恢复**：校验失败不立即放弃，宽召回后再判。

## 下一日

Day 39：Agent 工具链与多轮记忆深化。
"""


def _day38_api_cheatsheet() -> str:
    return """# Retry API 速查手册

| 方法 | 路径 |
|------|------|
| GET | `/api/knowledge/validation-config` |
| PUT | `/api/knowledge/validation-config` |
| POST | `/api/knowledge/validation-preview` |
| POST | `/api/knowledge/validation-retry-preview` |
| POST | `/api/chat` → `validation.retries` |
"""


def _architecture_day38() -> str:
    return """# Day 38 架构设计 — 多轮 Self-RAG 校验重试

## 1. 重试分层

```mermaid
flowchart TD
    CHAT["/api/chat"] --> VAL[validate]
    VAL -->|fail| RETRY[fetch_citations_retry]
    RETRY --> VAL2[re-validate]
    VAL2 -->|still fail| REFUSE[refuse_on_fail]
    CFG[ValidationConfig] --> VAL
    CFG --> RETRY
```

## 2. 组件

| 组件 | 职责 |
|------|------|
| validation_retry.py | apply_validation_retry 循环 |
| fetch_citations_retry | 强制 rag_wide + pool boost |
| RoutingRetriever | intent_override 宽召回 |
"""


def _acceptance_day38() -> str:
    return """# Day 38 Retry 验收清单

- [ ] retry_demo / validation-retry-preview 绿
- [ ] chat 含 validation.retries
- [ ] test_chat_refuses_after_retry_exhausted 绿
- [ ] tests/day38/ 15 项全绿
"""


def _fix_day39_terms(content: str, name: str) -> str:
    if name == "27_Day40预习.md":
        return content
    subs = [
        ("# Day 37 ", "# Day 39 "),
        ("（Day 37）", "（Day 39）"),
        ("22_validation_retry精读.md", "22_react_agent精读.md"),
        ("22_answer_validator精读.md", "22_react_agent精读.md"),
        ("17_Retry_API速查手册", "17_ReAct_API速查手册"),
        ("17_Validation_API速查手册", "17_ReAct_API速查手册"),
        ("精读：validation_retry 与多轮 Self-RAG 重试管线", "精读：react_agent 与 ReAct 工具链管线"),
        ("精读：answer_validator 与 Self-RAG 校验管线", "精读：react_agent 与 ReAct 工具链管线"),
        ("## 一、citation_builder.py 全文", "## 一、react_agent.py 全文"),
        ("## 一、validation_retry.py 全文", "## 一、react_agent.py 全文"),
        ("## 一、answer_validator.py 全文", "## 一、react_agent.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、react_agent 完整源码"),
        ("## 二十一、validation_retry 完整源码", "## 二十一、react_agent 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、react_agent 全文嵌入"),
        ("## 四十、validation_retry 全文嵌入", "## 四十、react_agent 全文嵌入"),
        ("| 2 | `validation_retry.py` | retry + rag_wide |", "| 2 | `react_agent.py` | Thought/Action/Observation |"),
        ("| 2 | `answer_validator.py` | validate + score |", "| 2 | `react_agent.py` | Thought/Action/Observation |"),
        ("| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |", "| 2 | `react_agent.py` | Thought/Action/Observation |"),
        ("校验重试详解", "ReAct详解"),
        ("Retry 验收清单", "ReAct 验收清单"),
        ("与 Day 37 能力对照表", "与 Day 38 能力对照表"),
        ("| Day 37 答案校验 | Day 38 校验重试 |", "| Day 38 校验重试 | Day 39 ReAct Agent |"),
        ("Phase 3 · Day 38 · Retry", "Phase 4 · Day 39 · ReAct"),
        ("Phase 3 第十三日总结（Day 38）", "Phase 4 第一日总结（Day 39）"),
        ("ZL-NA-REQ-038", "ZL-NA-REQ-039"),
        ("v0.38.0", "v0.39.0"),
        ("retry_demo.py", "react_demo.py"),
        ("retry_api_demo.py", "react_api_demo.py"),
        ("validation-retry-preview", "react-preview"),
        ("apply_validation_retry", "ReActAgent.run"),
        ("fetch_citations_retry", "tool_executor.execute"),
        ("多轮 Self-RAG 校验重试", "手写 ReAct Agent"),
        ("校验失败恢复场景", "Agent工具调用场景"),
        ("多轮Self-RAG方法论", "ReAct与工具链方法论"),
        ("重试阈值与拒答实践", "步数上限与延迟预算实践"),
        ("tests/day38/", "tests/day39/"),
        ("day38/", "day39/"),
        ("15 项全绿", "17 项全绿"),
        ("validation_retry", "react_agent"),
        ("ValidationRetry", "ReActAgent"),
        ("agent_trace", "agent_trace"),
    ]
    return _apply_subs(content, subs)


def _day39_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day39_file01(),
        "10_ReAct验收清单.md": _acceptance_day39(),
        "11_ReAct详解.md": _day39_file11(),
        "17_ReAct_API速查手册.md": _day39_api_cheatsheet(),
        "18_与Day38能力对照表.md": _day39_file18(),
        "24_Phase4第一日总结.md": _day39_file24(),
    }


def _day39_file01() -> str:
    return """# Day 39 企业背景与今日任务

**需求**：ZL-NA-REQ-039 | **版本**：v0.39.0

## 背景

Day 38 被动重试已能恢复失败；今日交付 **手写 ReAct Agent** — LLM/规则规划 Thought → Action → Observation，全链路可审计。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | ReactConfig + ReActAgent + ToolExecutor |
| 下午 | Lab：react-preview + agent_trace 截图 |
| 晚自习 | 读 Day 40 LangChain Agent 预习 |

## 代码阅读顺序

1. `agent/react_config.py`
2. `agent/react_agent.py`
3. `api/agent.py`
4. `api/chat.py` agent_mode
5. `tests/day39/`
"""


def _day39_file11() -> str:
    return """# ReAct 详解（Day 39 专题）

## 1. 循环

```
Thought → Action → Observation → … → Final Answer
```

## 2. 工具

复用 Day 21 `ToolRegistry`：`faq_lookup`、`rag_search`、`intent_classify`

## 3. 可观测

`agent_trace[]` 每步含 thought/action/observation；`tools_used[]` 汇总。
"""


def _day39_file18() -> str:
    return """# Day 39 与 Day 38 能力对照表

| 维度 | Day 38 重试 | Day 39 ReAct |
|------|-------------|--------------|
| 决策 | 固定 rag_wide | Agent 选择工具 |
| 输出 | validation.retries | agent_trace + tools_used |
| API | validation-retry-preview | react-preview |
| chat | 被动重试 | agent_mode=true |
"""


def _day39_file24() -> str:
    return """# Phase 4 第一日总结（Day 39）

## Day 39 交付物

- agent/react_agent.py + react_config.py
- GET/PUT /api/agent/react-config
- POST /api/agent/react-preview
- chat agent_mode + agent_trace
- tests/day39/ 17 项全绿

## 下一日

Day 40：LangChain Agent 框架对比。
"""


def _day39_api_cheatsheet() -> str:
    return """# ReAct API 速查手册

| 方法 | 路径 |
|------|------|
| GET | `/api/agent/react-config` |
| PUT | `/api/agent/react-config` |
| POST | `/api/agent/react-preview` |
| POST | `/api/chat` + `agent_mode: true` |
"""


def _architecture_day39() -> str:
    return """# Day 39 架构设计 — 手写 ReAct Agent

```mermaid
flowchart TD
    CHAT["/api/chat agent_mode"] --> RA[ReActAgent]
    RA --> TE[ToolExecutor]
    TE --> FAQ[faq_lookup]
    TE --> RAG[rag_search]
    RA --> TRACE["agent_trace"]
    CFG[ReactConfig] --> RA
```
"""


def _acceptance_day39() -> str:
    return """# Day 39 ReAct 验收清单

- [ ] react_demo / react-preview 绿
- [ ] chat agent_mode 含 agent_trace
- [ ] tests/day39/ 17 项全绿
"""


def _fix_day40_terms(content: str, name: str) -> str:
    if name == "27_Day41预习.md":
        return content
    subs = [
        ("# Day 39 ", "# Day 40 "),
        ("（Day 39）", "（Day 40）"),
        ("22_react_agent精读.md", "22_agent_executor精读.md"),
        ("17_ReAct_API速查手册", "17_Executor_API速查手册"),
        ("精读：react_agent 与 ReAct 工具链管线", "精读：agent_executor 与框架工具注册管线"),
        ("## 一、citation_builder.py 全文", "## 一、agent_executor.py 全文"),
        ("## 一、react_agent.py 全文", "## 一、agent_executor.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、agent_executor 完整源码"),
        ("## 二十一、react_agent 完整源码", "## 二十一、agent_executor 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、agent_executor 全文嵌入"),
        ("## 四十、react_agent 全文嵌入", "## 四十、agent_executor 全文嵌入"),
        ("| 2 | `citation_builder.py` | rewrite + MockCrossEncoder |", "| 2 | `agent_executor.py` | invoke + intermediate_steps |"),
        ("| 2 | `react_agent.py` | Thought/Action/Observation |", "| 2 | `agent_executor.py` | invoke + intermediate_steps |"),
        ("ReAct详解", "AgentExecutor详解"),
        ("ReAct 验收清单", "Executor 验收清单"),
        ("与 Day 38 能力对照表", "与 Day 39 能力对照表"),
        ("| Day 38 校验重试 | Day 39 ReAct Agent |", "| Day 39 ReAct Agent | Day 40 AgentExecutor |"),
        ("Phase 4 · Day 39 · ReAct", "Phase 4 · Day 40 · Executor"),
        ("Phase 4 第一日总结（Day 39）", "Phase 4 第二日总结（Day 40）"),
        ("ZL-NA-REQ-039", "ZL-NA-REQ-040"),
        ("v0.39.0", "v0.40.0"),
        ("react_demo.py", "executor_demo.py"),
        ("react_api_demo.py", "executor_api_demo.py"),
        ("react-preview", "executor-preview"),
        ("ReActAgent.run", "AgentExecutor.invoke"),
        ("tool_executor.execute", "StructuredTool.run"),
        ("手写 ReAct Agent", "AgentExecutor 框架工具链"),
        ("ReAct与工具链方法论", "框架式工具注册方法论"),
        ("步数上限与延迟预算实践", "迭代上限与中间步骤实践"),
        ("tests/day39/", "tests/day40/"),
        ("day39/", "day40/"),
        ("17 项全绿", "17 项全绿"),
        ("react_agent", "agent_executor"),
        ("ReActAgent", "AgentExecutor"),
        ("agent_trace", "executor_trace"),
        ("agent_mode", "executor_mode"),
        ("max_steps", "max_iterations"),
        ("ReactConfig", "ExecutorConfig"),
    ]
    return _apply_subs(content, subs)


def _day40_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day40_file01(),
        "10_ReAct验收清单.md": _acceptance_day40(),
        "11_ReAct详解.md": _day40_file11(),
        "17_ReAct_API速查手册.md": _day40_api_cheatsheet(),
        "18_与Day38能力对照表.md": _day40_file18(),
        "24_Phase4第一日总结.md": _day40_file24(),
    }


def _day40_file01() -> str:
    return """# Day 40 企业背景与今日任务

**需求**：ZL-NA-REQ-040 | **版本**：v0.40.0

## 背景

Day 39 手写 ReAct 已可观测；今日交付 **AgentExecutor + StructuredTool** — 框架式工具注册与 invoke 循环，trace 与 ReAct 对齐。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | StructuredTool + tool_adapter + AgentExecutor |
| 下午 | Lab：executor-preview + intermediate_steps 截图 |
| 晚自习 | 读 Day 41 LangGraph 预习 |

## 代码阅读顺序

1. `agent/structured_tool.py`
2. `agent/tool_adapter.py`
3. `agent/agent_executor.py`
4. `api/agent.py` executor-config / executor-preview
5. `api/chat.py` executor_mode
6. `tests/day40/`
"""


def _day40_file11() -> str:
    return """# AgentExecutor 详解（Day 40 专题）

## 1. StructuredTool

`@tool` 装饰器注册函数 → OpenAI function schema → `StructuredTool.run()`

## 2. invoke 循环

```
plan → tool.run → observation → … → Final Answer
```

## 3. 与 ReAct 对齐

`ExecutorStep` 字段与 Day 39 `ReactStep` 一致；`executor_trace` 可对照 `agent_trace`。
"""


def _day40_file18() -> str:
    return """# Day 40 与 Day 39 能力对照表

| 维度 | Day 39 ReAct | Day 40 AgentExecutor |
|------|--------------|----------------------|
| 工具 | ToolExecutor 直调 | StructuredTool.run |
| 入口 | ReActAgent.run | AgentExecutor.invoke |
| 配置 | ReactConfig.max_steps | ExecutorConfig.max_iterations |
| API | react-preview | executor-preview |
| chat | agent_mode | executor_mode |
| trace | agent_trace | executor_trace |
"""


def _day40_file24() -> str:
    return """# Phase 4 第二日总结（Day 40）

## 交付

- StructuredTool + @tool 装饰器
- AgentExecutor.invoke + intermediate_steps
- executor-config / executor-preview API
- chat executor_mode → executor_trace

## 验收

- tests/day40/ 17 项全绿
- delivery_check day01-day40 全绿
"""


def _day40_api_cheatsheet() -> str:
    return """# Executor API 速查（Day 40）

```
GET  /api/agent/executor-config
PUT  /api/agent/executor-config
POST /api/agent/executor-preview
POST /api/chat  { "executor_mode": true }
```

响应字段：`executor_trace`、`tools_used`、`intermediate_steps`（preview）
"""


def _architecture_day40() -> str:
    return """# Day 40 架构设计

## 模块

| 模块 | 职责 |
|------|------|
| structured_tool.py | @tool + OpenAI schema |
| tool_adapter.py | ToolRegistry → StructuredTool |
| agent_executor.py | invoke 循环 + mock planner |
| executor_config.py | max_iterations 等 |

```mermaid
flowchart TD
    CHAT["/api/chat executor_mode"] --> AE[AgentExecutor]
    AE --> ST[StructuredTool]
    ST --> TE[ToolExecutor]
    TE --> FAQ[faq_lookup]
    TE --> RAG[rag_search]
    AE --> TRACE["executor_trace"]
    CFG[ExecutorConfig] --> AE
```
"""


def _acceptance_day40() -> str:
    return """# Day 40 Executor 验收清单

- [ ] executor_demo / executor-preview 绿
- [ ] chat executor_mode 含 executor_trace
- [ ] tests/day40/ 17 项全绿
"""


def _fix_day41_terms(content: str, name: str) -> str:
    if name == "27_Day42预习.md":
        return content
    subs = [
        ("# Day 40 ", "# Day 41 "),
        ("（Day 40）", "（Day 41）"),
        ("22_agent_executor精读.md", "22_rag_agent_graph精读.md"),
        ("17_Executor_API速查手册", "17_Graph_API速查手册"),
        ("精读：agent_executor 与框架工具注册管线", "精读：rag_agent_graph 与状态图编排管线"),
        ("## 一、citation_builder.py 全文", "## 一、rag_agent_graph.py 全文"),
        ("## 一、agent_executor.py 全文", "## 一、rag_agent_graph.py 全文"),
        ("## 二十一、citation_builder 完整源码", "## 二十一、rag_agent_graph 完整源码"),
        ("## 二十一、agent_executor 完整源码", "## 二十一、rag_agent_graph 完整源码"),
        ("## 四十、citation_builder 全文嵌入", "## 四十、rag_agent_graph 全文嵌入"),
        ("## 四十、agent_executor 全文嵌入", "## 四十、rag_agent_graph 全文嵌入"),
        ("| 2 | `agent_executor.py` | invoke + intermediate_steps |", "| 2 | `rag_agent_graph.py` | planner → tool → answer |"),
        ("AgentExecutor详解", "StateGraph详解"),
        ("Executor 验收清单", "Graph 验收清单"),
        ("与 Day 39 能力对照表", "与 Day 40 能力对照表"),
        ("| Day 39 ReAct Agent | Day 40 AgentExecutor |", "| Day 40 AgentExecutor | Day 41 StateGraph |"),
        ("Phase 4 · Day 40 · Executor", "Phase 4 · Day 41 · StateGraph"),
        ("Phase 4 第二日总结（Day 40）", "Phase 4 第三日总结（Day 41）"),
        ("ZL-NA-REQ-040", "ZL-NA-REQ-041"),
        ("v0.40.0", "v0.41.0"),
        ("executor_demo.py", "graph_demo.py"),
        ("executor_api_demo.py", "graph_api_demo.py"),
        ("executor-preview", "graph-preview"),
        ("AgentExecutor.invoke", "RAGAgentGraph.invoke"),
        ("StructuredTool.run", "StateGraph node"),
        ("AgentExecutor 框架工具链", "StateGraph 状态图编排"),
        ("框架式工具注册方法论", "状态图编排方法论"),
        ("迭代上限与中间步骤实践", "节点路由与 node_path 实践"),
        ("tests/day40/", "tests/day41/"),
        ("day40/", "day41/"),
        ("17 项全绿", "17 项全绿"),
        ("agent_executor", "rag_agent_graph"),
        ("AgentExecutor", "RAGAgentGraph"),
        ("executor_trace", "graph_trace"),
        ("executor_mode", "graph_mode"),
        ("ExecutorConfig", "GraphConfig"),
        ("intermediate_steps", "node_path"),
    ]
    return _apply_subs(content, subs)


def _day41_minimal_overrides() -> dict[str, str]:
    return {
        "01_企业背景与今日任务.md": _day41_file01(),
        "10_ReAct验收清单.md": _acceptance_day41(),
        "11_ReAct详解.md": _day41_file11(),
        "17_ReAct_API速查手册.md": _day41_api_cheatsheet(),
        "18_与Day38能力对照表.md": _day41_file18(),
        "24_Phase4第一日总结.md": _day41_file24(),
    }


def _day41_file01() -> str:
    return """# Day 41 企业背景与今日任务

**需求**：ZL-NA-REQ-041 | **版本**：v0.41.0

## 背景

Day 40 AgentExecutor 已统一工具注册；今日交付 **StateGraph** — planner → tool_runner → answer 显式状态图，trace 含 node_path。

## 任务

| 时段 | 内容 |
|------|------|
| 上午 | StateGraph + AgentGraphState + RAGAgentGraph |
| 下午 | Lab：graph-preview + node_path 截图 |
| 晚自习 | 读 Day 42 人工审批预习 |

## 代码阅读顺序

1. `agent/graph_state.py`
2. `agent/state_graph.py`
3. `agent/rag_agent_graph.py`
4. `api/agent.py` graph-config / graph-preview
5. `api/chat.py` graph_mode
6. `tests/day41/`
"""


def _day41_file11() -> str:
    return """# StateGraph 详解（Day 41 专题）

## 1. 状态图

```
planner → tool_runner → answer
         ↑___________|
```

## 2. 节点

- `planner`：选择工具或 Final Answer
- `tool_runner`：StructuredTool.run
- `answer`：汇总 reply

## 3. 可观测

`graph_trace[]` 每步含 `node`；`node_path[]` 记录遍历路径。
"""


def _day41_file18() -> str:
    return """# Day 41 与 Day 40 能力对照表

| 维度 | Day 40 AgentExecutor | Day 41 StateGraph |
|------|----------------------|-----------------|
| 编排 | 线性 invoke | 显式节点 + 边 |
| 工具 | StructuredTool.run | tool_runner 节点 |
| API | executor-preview | graph-preview |
| chat | executor_mode | graph_mode |
| trace | executor_trace | graph_trace + node_path |
"""


def _day41_file24() -> str:
    return """# Phase 4 第三日总结（Day 41）

## 交付

- StateGraph 编译与 invoke
- RAGAgentGraph 三节点预置图
- graph-config / graph-preview API
- chat graph_mode → graph_trace

## 验收

- tests/day41/ 17 项全绿
- delivery_check day01-day41 全绿
"""


def _day41_api_cheatsheet() -> str:
    return """# Graph API 速查（Day 41）

```
GET  /api/agent/graph-config
PUT  /api/agent/graph-config
POST /api/agent/graph-preview
POST /api/chat  { "graph_mode": true }
```

响应字段：`graph_trace`、`tools_used`、`node_path`（preview）
"""


def _architecture_day41() -> str:
    return """# Day 41 架构设计

## 模块

| 模块 | 职责 |
|------|------|
| state_graph.py | add_node / compile / invoke |
| graph_state.py | AgentGraphState 共享状态 |
| rag_agent_graph.py | planner → tool_runner → answer |
| graph_config.py | max_iterations 等 |

```mermaid
flowchart TD
    CHAT["/api/chat graph_mode"] --> RG[RAGAgentGraph]
    RG --> P[planner]
    P --> T[tool_runner]
    T --> A[answer]
    T --> P
    P --> A
    RG --> TRACE["graph_trace + node_path"]
    CFG[GraphConfig] --> RG
```
"""


def _acceptance_day41() -> str:
    return """# Day 41 Graph 验收清单

- [ ] graph_demo / graph-preview 绿
- [ ] chat graph_mode 含 graph_trace
- [ ] tests/day41/ 17 项全绿
"""
