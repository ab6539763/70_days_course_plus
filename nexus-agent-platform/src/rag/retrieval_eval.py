"""
检索质量评估 — hit@1 与 A/B 分块对比

需求：ZL-NA-REQ-027
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.chunk_config import ChunkConfig
from rag.chunk_strategies import chunk_from_parsed
from rag.embedding_retriever import EmbeddingRetriever
from tools.parsers.base import ParsedDocument


@dataclass
class EvalQuery:
    """单条评估查询"""

    query: str
    expect_any: tuple[str, ...] = ()
    label: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvalQuery:
        expect = data.get("expect_any") or data.get("expect") or []
        return cls(
            query=str(data["query"]),
            expect_any=tuple(str(x) for x in expect),
            label=str(data.get("label", "")),
        )


@dataclass
class QueryEvalResult:
    """单查询评估结果"""

    query: str
    hit: bool
    top_score: float
    top_preview: str
    expect_any: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hit": self.hit,
            "top_score": round(self.top_score, 4),
            "top_preview": self.top_preview,
            "expect_any": list(self.expect_any),
        }


@dataclass
class ConfigEvalResult:
    """单配置完整评估"""

    config: ChunkConfig
    chunk_count: int
    hit_rate: float
    avg_top_score: float
    queries: list[QueryEvalResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "chunk_count": self.chunk_count,
            "hit_rate": round(self.hit_rate, 4),
            "avg_top_score": round(self.avg_top_score, 4),
            "queries": [q.to_dict() for q in self.queries],
        }


def build_retriever_for_doc(
    doc: ParsedDocument,
    config: ChunkConfig,
) -> EmbeddingRetriever:
    """用指定配置对单文档分块并构建临时检索器"""
    config.validate()
    chunks = chunk_from_parsed(
        doc,
        strategy=config.strategy,
        chunk_size=config.chunk_size,
        overlap=config.overlap,
    )
    return EmbeddingRetriever(chunks)


def evaluate_query(
    retriever: EmbeddingRetriever,
    eval_query: EvalQuery,
    *,
    top_k: int = 1,
) -> QueryEvalResult:
    results = retriever.search(eval_query.query, top_k=top_k)
    if not results:
        return QueryEvalResult(
            query=eval_query.query,
            hit=False,
            top_score=0.0,
            top_preview="",
            expect_any=eval_query.expect_any,
        )

    top = results[0]
    text = top.chunk.text
    hit = True
    if eval_query.expect_any:
        hit = any(kw in text for kw in eval_query.expect_any)

    return QueryEvalResult(
        query=eval_query.query,
        hit=hit,
        top_score=top.score,
        top_preview=top.preview(80),
        expect_any=eval_query.expect_any,
    )


def evaluate_config(
    doc: ParsedDocument,
    config: ChunkConfig,
    queries: list[EvalQuery],
) -> ConfigEvalResult:
    """对一份 ParsedDocument 评估分块配置"""
    retriever = build_retriever_for_doc(doc, config)
    query_results = [evaluate_query(retriever, q) for q in queries]
    hits = sum(1 for r in query_results if r.hit)
    total = len(query_results) or 1
    avg_score = sum(r.top_score for r in query_results) / total

    return ConfigEvalResult(
        config=config,
        chunk_count=retriever.chunk_count,
        hit_rate=hits / total,
        avg_top_score=avg_score,
        queries=query_results,
    )


def run_ab_experiment(
    doc: ParsedDocument,
    configs: list[ChunkConfig],
    queries: list[EvalQuery],
) -> list[ConfigEvalResult]:
    """多配置 A/B 对比，按 hit_rate 降序"""
    results = [evaluate_config(doc, cfg, queries) for cfg in configs]
    results.sort(key=lambda r: (-r.hit_rate, -r.avg_top_score, r.chunk_count))
    return results


def pick_best_config(results: list[ConfigEvalResult]) -> ConfigEvalResult | None:
    return results[0] if results else None
