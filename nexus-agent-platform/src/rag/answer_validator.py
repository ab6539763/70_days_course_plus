"""
Self-RAG 答案校验 — 引用与回复一致性打分

在 LLM 生成后，用 citations 的 preview / matched_tokens 校验 reply 是否被支撑。

需求：ZL-NA-REQ-037
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from rag.validation_config import MODE_STRICT, ValidationConfig

_TOKEN_SPLIT = re.compile(r"[\s,，。！？；;、·\-—]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]{2,}")


@dataclass(frozen=True)
class ValidationResult:
    """单条答案校验结果 — 供审计与 preview API"""

    query: str
    reply: str
    passed: bool
    score: float
    reason: str
    citation_coverage: float
    matched_citation_ranks: tuple[int, ...]
    refused: bool = False
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "reply": self.reply,
            "passed": self.passed,
            "score": round(self.score, 4),
            "reason": self.reason,
            "citation_coverage": round(self.citation_coverage, 4),
            "matched_citation_ranks": list(self.matched_citation_ranks),
            "refused": self.refused,
            "retries": self.retries,
        }


def _extract_tokens(text: str) -> set[str]:
    """从文本提取可用于 overlap 的关键词"""
    text = (text or "").strip().lower()
    if not text:
        return set()

    tokens: set[str] = set()
    for part in _TOKEN_SPLIT.split(text):
        part = part.strip()
        if len(part) >= 2:
            tokens.add(part)
        elif part:
            tokens.add(part)

    for run in _CJK_RUN.findall(text):
        tokens.add(run)
        if len(run) >= 4:
            for i in range(len(run) - 1):
                tokens.add(run[i : i + 2])

    return {t for t in tokens if len(t) >= 2 or t.isdigit()}


def _citation_text(citation: dict[str, Any]) -> str:
    preview = str(citation.get("preview") or "")
    matched = " ".join(str(t) for t in (citation.get("matched_tokens") or []))
    source = str(citation.get("source") or "")
    return f"{preview} {matched} {source}".strip().lower()


class AnswerValidator(ABC):
    """答案校验器抽象接口"""

    @abstractmethod
    def validate(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult:
        """校验 reply 是否被 citations 支撑"""


class RuleBasedAnswerValidator(AnswerValidator):
    """
    规则表校验器 — 基于 token overlap，无 LLM 依赖

    score = citation_coverage * 0.6 + query_coverage * 0.4
    strict 模式要求 citation_coverage >= 0.5 且 score >= min_score
    """

    def __init__(self, *, config: ValidationConfig | None = None) -> None:
        self._config = config or ValidationConfig()

    @property
    def config(self) -> ValidationConfig:
        return self._config

    def validate(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult:
        query = (query or "").strip()
        reply = (reply or "").strip()
        cfg = self._config

        if not cfg.enabled:
            return ValidationResult(
                query=query,
                reply=reply,
                passed=True,
                score=1.0,
                reason="校验已关闭",
                citation_coverage=1.0,
                matched_citation_ranks=(),
            )

        if not reply:
            return ValidationResult(
                query=query,
                reply=reply,
                passed=False,
                score=0.0,
                reason="回复为空",
                citation_coverage=0.0,
                matched_citation_ranks=(),
            )

        if reply.startswith("[FAQ 直答"):
            return ValidationResult(
                query=query,
                reply=reply,
                passed=True,
                score=1.0,
                reason="FAQ 直答跳过校验",
                citation_coverage=1.0,
                matched_citation_ranks=(),
            )

        if not citations:
            return ValidationResult(
                query=query,
                reply=reply,
                passed=False,
                score=0.0,
                reason="无可用引用",
                citation_coverage=0.0,
                matched_citation_ranks=(),
            )

        reply_tokens = _extract_tokens(reply)
        query_tokens = _extract_tokens(query)
        matched_ranks: list[int] = []
        reply_cite_tokens: set[str] = set()

        for cite in citations:
            cite_tokens = _extract_tokens(_citation_text(cite))
            overlap = reply_tokens & cite_tokens
            reply_cite_tokens |= overlap
            if overlap or (query_tokens & cite_tokens and reply_tokens & query_tokens):
                rank = int(cite.get("rank") or len(matched_ranks) + 1)
                matched_ranks.append(rank)

        citation_coverage = len(matched_ranks) / max(1, len(citations))
        support_score = len(reply_cite_tokens) / max(1, len(reply_tokens))
        query_in_reply = len(query_tokens & reply_tokens) / max(1, len(query_tokens))

        if not reply_cite_tokens and len(reply_tokens) > 1:
            score = min(query_in_reply * 0.25, 0.2)
            citation_coverage = 0.0
            matched_ranks = []
        else:
            score = citation_coverage * 0.55 + support_score * 0.35 + query_in_reply * 0.1

        passed = score >= cfg.min_score
        if cfg.mode == MODE_STRICT:
            passed = passed and citation_coverage >= 0.5 and support_score >= 0.15

        if passed:
            reason = f"引用覆盖率 {citation_coverage:.0%}，综合分 {score:.2f}"
        elif not matched_ranks:
            reason = "回复与引用内容无明显重叠"
        else:
            reason = f"综合分 {score:.2f} 低于阈值 {cfg.min_score:.2f}"

        return ValidationResult(
            query=query,
            reply=reply,
            passed=passed,
            score=score,
            reason=reason,
            citation_coverage=citation_coverage,
            matched_citation_ranks=tuple(sorted(set(matched_ranks))),
        )
