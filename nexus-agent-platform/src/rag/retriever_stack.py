"""
检索装饰器链工具 — 从外层 Routing/Expanding 剥到目标 Retriever

需求：ZL-NA-REQ-031（演示与测试共用）
"""

from __future__ import annotations

from typing import TypeVar

from rag.expanding_retriever import ExpandingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.reranking_retriever import RerankingRetriever
from rag.rewriting_retriever import RewritingRetriever
from rag.routing_retriever import RoutingRetriever

T = TypeVar("T")


def unwrap_retriever(retriever, target_type: type[T]) -> T:
    """沿 inner 链查找目标 Retriever 类型"""
    current = retriever
    while current is not None:
        if isinstance(current, target_type):
            return current
        inner = getattr(current, "inner", None)
        if inner is None:
            break
        current = inner
    raise RuntimeError(f"expected {target_type.__name__} in retriever stack, got {type(retriever).__name__}")


def peel_outer_layers(retriever):
    """剥掉 Routing / Expanding 外层，返回内层（Rewriting 或更深）"""
    current = retriever
    while isinstance(current, (RoutingRetriever, ExpandingRetriever)):
        current = current.inner
    return current


def find_hybrid(retriever) -> HybridRetriever:
    return unwrap_retriever(retriever, HybridRetriever)


def find_reranking(retriever) -> RerankingRetriever:
    return unwrap_retriever(retriever, RerankingRetriever)


def find_rewriting(retriever) -> RewritingRetriever:
    return unwrap_retriever(retriever, RewritingRetriever)
