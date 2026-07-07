"""
向量运算 — 余弦相似度等（纯标准库）

需求：ZL-NA-REQ-020
"""

from __future__ import annotations

import math
from typing import Sequence


def dot_product(a: Sequence[float], b: Sequence[float]) -> float:
    """向量点积"""
    if len(a) != len(b):
        raise ValueError("向量维度不一致")
    return sum(x * y for x, y in zip(a, b))


def vector_norm(v: Sequence[float]) -> float:
    """L2 范数"""
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """
    余弦相似度，取值约 [-1, 1]。

    零向量时返回 0.0。
    """
    if len(a) != len(b):
        raise ValueError("向量维度不一致")
    na = vector_norm(a)
    nb = vector_norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot_product(a, b) / (na * nb)


def normalize_vector(v: list[float]) -> list[float]:
    """单位化向量（用于展示）"""
    n = vector_norm(v)
    if n == 0.0:
        return list(v)
    return [x / n for x in v]
