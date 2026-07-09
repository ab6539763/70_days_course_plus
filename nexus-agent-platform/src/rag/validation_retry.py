"""
多轮 Self-RAG 校验重试 — 校验失败后宽召回重检索

校验未通过时按 rag_wide 策略重新检索 citations，可选再生成 reply，
在拒答前尽量恢复可审计的正确回答。

需求：ZL-NA-REQ-038
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any, Callable

from rag.answer_validator import RuleBasedAnswerValidator, ValidationResult
from rag.validation_config import REFUSAL_MESSAGE, ValidationConfig


@dataclass(frozen=True)
class ValidationRetryOutcome:
    """校验 + 重试后的最终输出"""

    validation: ValidationResult
    citations: list[dict[str, Any]]
    cite_data: dict[str, Any]
    reply: str
    refused: bool = False


def apply_validation_retry(
    store,
    query: str,
    reply: str,
    citations: list[dict[str, Any]],
    cite_data: dict[str, Any],
    *,
    regenerate_fn: Callable[[], str] | None = None,
) -> ValidationRetryOutcome | None:
    """
  按 validation_config 执行校验；失败且 retry_on_fail 时宽召回重检索。

  Returns:
      None 表示校验关闭（与 Day37 行为一致，由调用方跳过 validation 字段）
    """
    cfg: ValidationConfig = store.get_validation_config()
    if not cfg.enabled:
        return None

    validator = RuleBasedAnswerValidator(config=cfg)
    result = validator.validate(query, reply, citations)
    current_reply = reply
    current_citations = citations
    current_cite = cite_data
    retries = 0

    if not result.passed and cfg.retry_on_fail and cfg.max_retries > 0:
        while not result.passed and retries < cfg.max_retries:
            retries += 1
            current_cite = store.fetch_citations_retry(query, attempt=retries)
            current_citations = current_cite.get("citations") or []
            if regenerate_fn is not None:
                current_reply = regenerate_fn()
            result = validator.validate(query, current_reply, current_citations)
        result = replace(result, retries=retries)

    refused = not result.passed and cfg.refuse_on_fail
    if refused:
        current_reply = f"[校验未通过] {REFUSAL_MESSAGE}"
        result = replace(result, refused=True, retries=retries)

    return ValidationRetryOutcome(
        validation=result,
        citations=current_citations,
        cite_data=current_cite,
        reply=current_reply,
        refused=refused,
    )
