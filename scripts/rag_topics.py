"""Shared per-day facts + content generators for the Day 35-38 RAG-pipeline
days (Query Expansion / Adaptive Routing / Self-RAG Validation / Validation
Retry). Like the Day 39-44 "Agent" family, these four days were authored by
copy-pasting a shared template and only patching a handful of override files
(01/03/04/10/11/17/18/24 where present); the remaining narrative files kept
the *previous* day's config names, API paths, and case studies verbatim
(e.g. Day 35's homework literally imports ``rag.citation_config.RouteConfig``
— Day 34/36 leftovers — instead of Day 35's own ``ExpansionConfig``).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RagDay:
    day: int
    req: str
    ver: str
    topic: str
    subtitle: str
    modules: tuple[tuple[str, str], ...]
    api_config: str
    api_preview: str
    api_extra: tuple[str, ...]
    config_class: str
    config_field: str
    constants_name: str
    demo_files: tuple[str, ...]
    review_file: str
    tests_dir: str
    tests_count: int
    core_class: str
    prev_day: int
    prev_topic: str
    next_day: int
    next_topic: str
    key_sentence: str
    story_problem: str
    story_solution: str
    case_studies: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)
    quiz: tuple[tuple[str, str], ...] = field(default_factory=tuple)


DAYS: dict[int, RagDay] = {
    35: RagDay(
        day=35, req="ZL-NA-REQ-035", ver="v0.35.0",
        topic="多查询扩展（Query Expansion / HyDE）",
        subtitle="rewrite → hybrid → rerank → expansion.queries + merged citations",
        modules=(
            ("rag/query_expander.py", "QueryExpander — Template / HyDE mock 扩展"),
            ("rag/expanding_retriever.py", "ExpandingRetriever — 多路 search + merge"),
            ("rag/expansion_config.py", "ExpansionConfig — enabled / max_queries / per_query_top_k"),
            ("rag/result_merger.py", "merge_retrieval_results — chunk_id 去重合并"),
        ),
        api_config="/api/knowledge/expansion-config", api_preview="/api/knowledge/expansion-preview",
        api_extra=(), config_class="ExpansionConfig", config_field="expansion_config",
        constants_name="EXPANSION_QUERIES",
        demo_files=("day35/expansion_demo.py", "day35/expansion_api_demo.py"),
        review_file="day35/phase3_expansion_review.py",
        tests_dir="tests/day35/", tests_count=20, core_class="ExpandingRetriever",
        prev_day=34, prev_topic="引用溯源（Citation Traceability）",
        next_day=36, next_topic="自适应路由（Query Router）",
        key_sentence="Day 34 让回答有据可查；Day 35 让检索更广更全 — 一条问句拓展成多条 query 再合并召回。",
        story_problem="质检发现「理财安全吗」这类模糊问句，单条 query 召回经常漏掉真正相关的 chunk，Recall 不够宽。",
        story_solution="引入 QueryExpander：把一条问句用模板/HyDE mock 拓展成多条候选 query，ExpandingRetriever 多路并发召回后按 chunk_id 去重合并，再进入既有的 rerank → citations 管线。",
        case_studies=(
            ("模糊问句拓宽召回", "理财安全吗", "扩展出「投资风险」「资金安全」等候选 query，多路合并召回"),
            ("已有精确问句无需扩展", "客服电话多少", "扩展仍生成候选 query，但去重后对最终 top-1 影响很小"),
            ("关闭扩展回退", "PUT enabled=false", "行为回退到 Day34 单 query 检索"),
        ),
        quiz=(
            ("QueryExpander 有哪两种扩展模式？", "templates（模板规则）与 hyde_mock（假设文档）"),
            ("多路召回后如何去重？", "按 chunk_id 保留最高分（merge_retrieval_results）"),
        ),
    ),
    36: RagDay(
        day=36, req="ZL-NA-REQ-036", ver="v0.36.0",
        topic="自适应路由（Query Router）",
        subtitle="route → expand? → rewrite → hybrid → rerank → citations",
        modules=(
            ("rag/query_router.py", "RuleBasedQueryRouter — faq_fast / rag_standard / rag_wide"),
            ("rag/routing_retriever.py", "RoutingRetriever — 动态 expand/rewrite 开关"),
            ("rag/route_config.py", "RouteConfig — enabled / fallback_intent"),
        ),
        api_config="/api/knowledge/route-config", api_preview="/api/knowledge/route-preview",
        api_extra=(), config_class="RouteConfig", config_field="route_config",
        constants_name="ROUTE_QUERIES",
        demo_files=("day36/route_demo.py", "day36/route_api_demo.py"),
        review_file="day36/phase3_route_review.py",
        tests_dir="tests/day36/", tests_count=20, core_class="RoutingRetriever",
        prev_day=35, prev_topic="多查询扩展（Query Expansion / HyDE）",
        next_day=37, next_topic="Self-RAG 答案校验",
        key_sentence="Day 35 让检索更广；Day 36 让管线更省 — 按问句意图动态决定是否要 expand/rewrite。",
        story_problem="Day35 全量扩展后，简单的「客服电话多少」这类 FAQ 问句也要走多路召回 + 改写，延迟不必要地增加。",
        story_solution="引入 RuleBasedQueryRouter：按意图分三档路由——faq_fast 跳过 expand/rewrite 直接查，rag_standard 走常规管线，rag_wide 对模糊/合规问句开启全部增强手段。",
        case_studies=(
            ("FAQ 快路径", "客服电话多少", "路由到 faq_fast，跳过 expand + rewrite，直接检索"),
            ("常规检索", "年化收益怎么样", "路由到 rag_standard，走默认管线"),
            ("宽召回慢路径", "理财安全吗", "路由到 rag_wide，开启 expand + rewrite 全增强"),
        ),
        quiz=(
            ("QueryRouter 的三档意图是？", "faq_fast / rag_standard / rag_wide"),
            ("路由由谁计算，何时生效？", "RuleBasedQueryRouter 按关键词规则；每次 search 调用时动态生效"),
        ),
    ),
    37: RagDay(
        day=37, req="ZL-NA-REQ-037", ver="v0.37.0",
        topic="Self-RAG 答案校验",
        subtitle="route → expand? → rewrite → hybrid → rerank → citations → LLM → validate",
        modules=(
            ("rag/answer_validator.py", "RuleBasedAnswerValidator — 引用-回复一致性打分"),
            ("rag/validation_config.py", "ValidationConfig — enabled / min_score / refuse_on_fail"),
        ),
        api_config="/api/knowledge/validation-config", api_preview="/api/knowledge/validation-preview",
        api_extra=(), config_class="ValidationConfig", config_field="validation_config",
        constants_name="VALIDATION_CASES",
        demo_files=("day37/validation_demo.py", "day37/validation_api_demo.py"),
        review_file="day37/phase3_validation_review.py",
        tests_dir="tests/day37/", tests_count=21, core_class="RuleBasedAnswerValidator",
        prev_day=36, prev_topic="自适应路由（Query Router）",
        next_day=38, next_topic="多轮 Self-RAG 校验重试",
        key_sentence="Day 36 让管线更省；Day 37 让回答更准 — 生成后校验 citations 是否真的支撑 reply。",
        story_problem="合规部反馈：虽然每条回答都带了 citations，但 LLM 仍偶发「引用是 A、回答是 B」的答非所问。",
        story_solution="实现 RuleBasedAnswerValidator，在 chat API 返回前校验 reply 与 citations 的 token 重合度打分；分数低于 min_score 且 refuse_on_fail 时拒答。",
        case_studies=(
            ("回答与引用一致", "客服电话多少 → 客服热线是 400-888-1234", "校验通过，正常返回"),
            ("答非所问", "年化收益怎么样 → 今天北京天气晴朗", "校验分数低，refuse_on_fail=true 时拒答"),
            ("边界分数", "min_score 附近的部分匹配回答", "验证 clamp 与阈值比较逻辑"),
        ),
        quiz=(
            ("AnswerValidator 打分依据是什么？", "reply 与 citations 的 token 重合覆盖率"),
            ("refuse_on_fail 语义？", "校验不通过时用统一拒答文案替换原始 reply"),
        ),
    ),
    38: RagDay(
        day=38, req="ZL-NA-REQ-038", ver="v0.38.0",
        topic="多轮 Self-RAG 校验重试",
        subtitle="validate 失败 → rag_wide 重检索 → 再校验",
        modules=(
            ("rag/validation_retry.py", "apply_validation_retry — 校验失败后 rag_wide 重检索再校验"),
        ),
        api_config="/api/knowledge/validation-config", api_preview="/api/knowledge/validation-retry-preview",
        api_extra=(), config_class="ValidationConfig", config_field="validation_config",
        constants_name="RETRY_CASES",
        demo_files=("day38/retry_demo.py", "day38/retry_api_demo.py"),
        review_file="day38/phase3_retry_review.py",
        tests_dir="tests/day38/", tests_count=15, core_class="apply_validation_retry",
        prev_day=37, prev_topic="Self-RAG 答案校验",
        next_day=39, next_topic="手写 ReAct Agent",
        key_sentence="Day 37 让回答更准；Day 38 让校验失败后还能自动补救 — 强制 rag_wide 重检索再校验一次。",
        story_problem="Day37 校验拒答后用户体验很差——机器人直接说「无法确认」，一次机会就放弃了，没有给系统补救的余地。",
        story_solution="实现 apply_validation_retry：校验失败且 retry_on_fail 时，用 rag_wide 意图强制放大检索池重新召回，再校验一次；仍失败才真正拒答。",
        case_studies=(
            ("首次校验失败后补救成功", "年化收益怎么样（首次窄召回未命中）", "rag_wide 重检索后命中含数字的 chunk，二次校验通过"),
            ("重试仍失败", "彻底答非所问的场景", "二次校验仍不通过，最终拒答并标记 retries"),
            ("关闭重试", "retry_on_fail=false", "行为回退到 Day37 单次校验"),
        ),
        quiz=(
            ("重试时用什么检索意图？", "rag_wide（放大检索池）"),
            ("validation.retries 字段记录什么？", "本次请求是否发生了重试及重试次数"),
        ),
    ),
}


def get(day: int) -> RagDay:
    return DAYS[day]
