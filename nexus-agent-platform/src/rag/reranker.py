"""
交叉编码器重排 — 对 hybrid 召回候选逐对精排

MockCrossEncoder 用 query-chunk 双向 token 覆盖 + 子串命中模拟
交叉编码器行为，无需加载 HuggingFace 模型。

需求：ZL-NA-REQ-032
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from rag.retriever import RetrievalResult, _tokenize

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+")


class Reranker(ABC):
    """重排器抽象接口"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """对候选列表按 query-chunk 相关性重排并截断"""


class MockCrossEncoderReranker(Reranker):
    """
    教学用 Mock 交叉编码器

    与 bi-encoder（向量检索）不同，逐对计算 query 与 chunk 的细粒度交互：
    - 完整子串命中加权
    - token 覆盖率
    - 连续 bigram 共现奖励
    - 过长 chunk 轻微惩罚（降低噪声段落排名）
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not candidates:
            return []

        scored: list[RetrievalResult] = []
        for item in candidates:
            score = score_pair(query, item.chunk.text)
            if score <= 0:
                continue
            scored.append(
                RetrievalResult(
                    chunk=item.chunk,
                    score=score,
                    matched_tokens=item.matched_tokens,
                )
            )

        scored.sort(key=lambda r: (-r.score, r.chunk.index))
        return scored[: max(1, top_k)]


def score_pair(query: str, text: str) -> float:
    """模拟 cross-encoder 对 (query, chunk) 的相关性打分"""
    q = query.strip().lower()
    t = text.lower()
    if not q or not t:
        return 0.0

    if q in t:
        return 1.0

    tokens = _tokenize(q)
    if not tokens:
        return 0.0

    matched = [tok for tok in tokens if tok in t]
    coverage = len(matched) / len(tokens)

    bigram_bonus = _bigram_overlap(q, t)
    length_penalty = min(len(t) / 2500.0, 0.12)

    raw = coverage * 0.65 + bigram_bonus * 0.35 - length_penalty
    return max(0.0, min(1.0, raw))


def _bigram_overlap(query: str, text: str) -> float:
    """查询连续二字/词在文本中共现的比例"""
    units: list[str] = []
    for part in _TOKEN_PATTERN.findall(query):
        units.append(part.lower())
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 2:
            for i in range(len(part) - 1):
                units.append(part[i : i + 2].lower())

    if not units:
        return 0.0

    hits = sum(1 for u in units if u in text)
    return hits / len(units)
