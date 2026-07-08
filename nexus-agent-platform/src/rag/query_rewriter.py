"""
查询改写 — 口语问句规范化为检索友好 query

RuleBasedQueryRewriter 用可审计规则表将指代、口语映射为
与 sample_docs 对齐的关键词（年化收益率、联系方式、投资风险等）。

需求：ZL-NA-REQ-033
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.rewrite_config import RewriteConfig

# (rule_id, pattern, replacement) — 顺序优先，先匹配先应用
DEFAULT_RULES: tuple[tuple[str, str, str], ...] = (
    ("colloquial_yield", r"那个.{0,12}理财.{0,8}赚", "年化收益率是多少"),
    ("colloquial_yield_short", r"能赚多少|收益怎么样|赚多少", "年化收益率"),
    ("annual_yield", r"年化.{0,4}多少|收益率.{0,4}多少", "年化收益率可达"),
    ("risk_colloquial", r"有风险吗|会不会亏|安全吗", "投资有风险"),
    ("contact_phone", r"客服.{0,6}电话|联系电话|怎么联系|电话多少", "联系方式客服电话"),
    ("manager_phone", r"客户经理.{0,4}手机", "客户经理手机"),
    ("internal_doc", r"内部资料|保密", "内部资料禁止外传"),
    ("pdf_upload", r"怎么上传.{0,6}pdf|pdf.{0,6}上传", "如何上传PDF文档"),
)


@dataclass(frozen=True)
class RewriteResult:
    """单条改写结果 — 供审计与 preview API"""

    original: str
    rewritten: str
    changed: bool
    rule_id: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "original": self.original,
            "rewritten": self.rewritten,
            "changed": self.changed,
            "rule_id": self.rule_id,
        }


class QueryRewriter(ABC):
    """查询改写器抽象接口"""

    @abstractmethod
    def rewrite(self, query: str) -> RewriteResult:
        """将用户问句改写为检索 query"""


class RuleBasedQueryRewriter(QueryRewriter):
    """
    规则表改写器 — 可审计、无 LLM 依赖

    流程：normalize → 逐条 regex 匹配 → 命中则替换并截断长度
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, str], ...] | None = None,
        config: RewriteConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_RULES
        self._config = config or RewriteConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), repl)
            for rid, pat, repl in self._rules
        ]

    @property
    def config(self) -> RewriteConfig:
        return self._config

    def rewrite(self, query: str) -> RewriteResult:
        original = (query or "").strip()
        if not original:
            return RewriteResult(original="", rewritten="", changed=False)

        text = _normalize_query(original)
        rule_id: str | None = None

        for rid, pattern, replacement in self._compiled:
            if pattern.search(text):
                text = replacement
                rule_id = rid
                break

        text = text[: self._config.max_rewrite_len].strip()
        if not text and self._config.fallback_to_original:
            text = original

        changed = text != original
        return RewriteResult(
            original=original,
            rewritten=text,
            changed=changed,
            rule_id=rule_id,
        )


def _normalize_query(text: str) -> str:
    """全角空格、连续空白压缩"""
    t = text.replace("\u3000", " ").strip()
    t = re.sub(r"\s+", " ", t)
    return t
