"""
意图分类器 — 规则路由 + Prompt 模板选择

Day 18 MVP 使用关键词规则引擎；Day 19+ 可替换为 LLM 分类。
输出模板名供 ChatAssistant.apply_template 使用。

需求：ZL-NA-REQ-018
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from prompts.registry import PromptRegistry, default_registry

# 意图 → 模板名映射
INTENT_TEMPLATE_MAP: dict[str, str] = {
    "rag_qa": "rag_qa",
    "doc_summary": "doc_summary",
    "compliance_review": "compliance_review",
    "product_faq": "product_faq",
    "general": "default_assistant",
}

# 关键词规则（意图: 关键词列表）
DEFAULT_KEYWORD_RULES: dict[str, list[str]] = {
    "compliance_review": ["合规", "审阅", "审查", "宣传语", "敏感", "违规"],
    "doc_summary": ["总结", "摘要", "概括", "要点", "汇总", "归纳"],
    "product_faq": ["理财", "产品", "收益", "基金", "年化", "风险"],
    "rag_qa": ["文档", "资料", "根据", "查询", "说明书", "条款", "文件中"],
}

# 同分时的优先级（靠前优先）
INTENT_PRIORITY: tuple[str, ...] = (
    "compliance_review",
    "doc_summary",
    "product_faq",
    "rag_qa",
    "general",
)

ContextProvider = Callable[[], str]


@dataclass
class IntentMatch:
    """意图分类结果"""

    intent: str
    template_name: str
    confidence: float
    matched_keywords: list[str] = field(default_factory=list)
    user_text: str = ""

    def summary(self) -> str:
        kw = ", ".join(self.matched_keywords) if self.matched_keywords else "（默认）"
        return (
            f"意图={self.intent} → 模板={self.template_name} | "
            f"置信度={self.confidence:.0%} | 命中={kw}"
        )


class RuleBasedIntentClassifier:
    """基于关键词打分的意图分类器"""

    def __init__(
        self,
        rules: dict[str, list[str]] | None = None,
        template_map: dict[str, str] | None = None,
        priority: tuple[str, ...] = INTENT_PRIORITY,
    ) -> None:
        self.rules = rules or DEFAULT_KEYWORD_RULES
        self.template_map = template_map or INTENT_TEMPLATE_MAP
        self.priority = priority

    def classify(self, text: str) -> IntentMatch:
        text = (text or "").strip()
        if not text:
            return self._default_match(text, confidence=0.5)

        scores: dict[str, tuple[int, list[str]]] = {}
        for intent, keywords in self.rules.items():
            matched = [kw for kw in keywords if kw in text]
            if matched:
                scores[intent] = (len(matched), matched)

        if not scores:
            return self._default_match(text, confidence=0.6)

        max_score = max(v[0] for v in scores.values())
        candidates = [k for k, v in scores.items() if v[0] == max_score]
        intent = self._pick_by_priority(candidates)
        _, matched = scores[intent]
        confidence = min(0.95, 0.55 + 0.1 * max_score)

        return IntentMatch(
            intent=intent,
            template_name=self.template_map.get(intent, "default_assistant"),
            confidence=confidence,
            matched_keywords=matched,
            user_text=text,
        )

    def _pick_by_priority(self, candidates: list[str]) -> str:
        for intent in self.priority:
            if intent in candidates:
                return intent
        return candidates[0]

    def _default_match(self, text: str, *, confidence: float) -> IntentMatch:
        return IntentMatch(
            intent="general",
            template_name=self.template_map.get("general", "default_assistant"),
            confidence=confidence,
            matched_keywords=[],
            user_text=text,
        )


class IntentRouter:
    """
    意图分类 + 模板变量构建 + 应用到 ChatAssistant

    将「用户说什么」映射到「用哪个 Prompt 模板」。
    """

    def __init__(
        self,
        *,
        classifier: RuleBasedIntentClassifier | None = None,
        registry: PromptRegistry | None = None,
        company: str = "智链科技",
        context_provider: ContextProvider | None = None,
        default_product: str = "稳健增值系列产品",
    ) -> None:
        self.classifier = classifier or RuleBasedIntentClassifier()
        self.registry = registry or default_registry
        self.company = company
        self.context_provider = context_provider
        self.default_product = default_product

    def classify(self, text: str) -> IntentMatch:
        return self.classifier.classify(text)

    def build_variables(self, match: IntentMatch) -> dict[str, str]:
        """根据意图构建模板变量"""
        base: dict[str, str] = {"company": self.company}
        name = match.template_name
        text = match.user_text

        if name == "rag_qa":
            context = self.context_provider() if self.context_provider else "（暂无检索上下文）"
            return {**base, "context": context}
        if name == "doc_summary":
            return {**base, "max_points": "3", "document": text}
        if name == "compliance_review":
            return {**base, "text": text}
        if name == "product_faq":
            return {**base, "product_name": self.default_product}
        return base

    def route_and_apply(self, assistant, user_text: str) -> IntentMatch:
        """
        分类用户输入，切换 assistant 的 Prompt 模板。

        Args:
            assistant: ChatAssistant 实例
            user_text: 用户原始输入
        """
        match = self.classify(user_text)
        variables = self.build_variables(match)
        assistant.apply_template(match.template_name, variables=variables)
        return match
