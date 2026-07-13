"""
多查询扩展 — 模板变体与 HyDE mock

将单条用户问句扩展为多条检索 query，供 ExpandingRetriever 并行召回后合并去重。

需求：ZL-NA-REQ-035
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rag.expansion_config import ExpansionConfig, MODE_HYDE_MOCK, MODE_TEMPLATES

# (rule_id, pattern, expansion_queries)
DEFAULT_EXPANSION_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "safety_risk",
        r"安全吗|会不会亏|理财安全|保本",
        ("投资风险", "投资有风险", "风险揭示"),
    ),
    (
        "yield",
        r"收益|赚多少|年化|利率",
        ("年化收益率", "收益率可达", "理财产品收益"),
    ),
    (
        "contact",
        r"电话|联系|客服|怎么找",
        ("联系方式客服电话", "客户经理手机", "客服热线"),
    ),
    (
        "compliance",
        r"合规|披露|说明书",
        ("风险揭示书", "产品说明书", "合规披露"),
    ),
    (
        "upload",
        r"上传|pdf|文档",
        ("如何上传PDF文档", "文档上传", "知识库上传"),
    ),
)


@dataclass(frozen=True)
class ExpansionResult:
    """多 query 扩展结果 — 供审计与 preview API"""

    original: str
    queries: tuple[str, ...]
    changed: bool
    mode: str
    rule_id: str | None = None

    def to_dict(self) -> dict[str, str | bool | list[str] | None]:
        return {
            "original": self.original,
            "queries": list(self.queries),
            "changed": self.changed,
            "mode": self.mode,
            "rule_id": self.rule_id,
        }


class QueryExpander(ABC):
    """查询扩展器抽象接口"""

    @abstractmethod
    def expand(self, query: str) -> ExpansionResult:
        """将用户问句扩展为多条检索 query"""


class TemplateQueryExpander(QueryExpander):
    """
    规则模板扩展 — 命中业务规则时追加同义检索 query

    流程：normalize → 逐条 regex → 合并去重 → 截断 max_queries
    """

    def __init__(
        self,
        *,
        rules: tuple[tuple[str, str, tuple[str, ...]], ...] | None = None,
        config: ExpansionConfig | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_EXPANSION_RULES
        self._config = config or ExpansionConfig()
        self._compiled = [
            (rid, re.compile(pat, re.IGNORECASE), qs)
            for rid, pat, qs in self._rules
        ]

    @property
    def config(self) -> ExpansionConfig:
        return self._config

    def expand(self, query: str) -> ExpansionResult:
        original = (query or "").strip()
        if not original:
            return ExpansionResult(
                original="",
                queries=(),
                changed=False,
                mode=MODE_TEMPLATES,
            )

        cfg = self._config
        seen: set[str] = set()
        ordered: list[str] = []

        def _add(q: str) -> None:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                ordered.append(q)

        if cfg.include_original:
            _add(original)

        rule_id: str | None = None
        for rid, pattern, extras in self._compiled:
            if pattern.search(original):
                rule_id = rid
                for eq in extras:
                    _add(eq)
                break

        if not rule_id:
            # 泛化：拆 token 作弱扩展
            tokens = re.findall(r"[\u4e00-\u9fff]{2,}", original)
            for tok in tokens[:2]:
                _add(tok)

        limited = tuple(ordered[: cfg.max_queries])
        changed = len(limited) > 1 or (
            len(limited) == 1 and limited[0] != original
        )
        return ExpansionResult(
            original=original,
            queries=limited if limited else (original,),
            changed=changed or len(limited) > 1,
            mode=MODE_TEMPLATES,
            rule_id=rule_id,
        )


class HyDEMockExpander(QueryExpander):
    """
    HyDE mock — 生成假设性文档片段作为额外检索 query

    教学实现：不调用 LLM，用模板拼接 hypothetical passage。
    """

    def __init__(self, config: ExpansionConfig | None = None) -> None:
        self._config = config or ExpansionConfig(mode=MODE_HYDE_MOCK)
        self._template = TemplateQueryExpander(config=self._config)

    @property
    def config(self) -> ExpansionConfig:
        return self._config

    def expand(self, query: str) -> ExpansionResult:
        original = (query or "").strip()
        if not original:
            return ExpansionResult(
                original="",
                queries=(),
                changed=False,
                mode=MODE_HYDE_MOCK,
            )

        hypo = (
            f"关于「{original}」，请参考产品说明书中的风险提示、"
            f"年化收益率说明与合规披露条款。"
        )
        base = self._template.expand(original)
        seen: set[str] = set()
        ordered: list[str] = []

        for q in (original, hypo, *base.queries):
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                ordered.append(q)

        limited = tuple(ordered[: self._config.max_queries])
        return ExpansionResult(
            original=original,
            queries=limited if limited else (original,),
            changed=len(limited) > 1,
            mode=MODE_HYDE_MOCK,
            rule_id=base.rule_id,
        )


def build_expander(config: ExpansionConfig | None = None) -> QueryExpander:
    """按配置构建扩展器"""
    cfg = config or ExpansionConfig()
    if cfg.mode == MODE_HYDE_MOCK:
        return HyDEMockExpander(config=cfg)
    return TemplateQueryExpander(config=cfg)
