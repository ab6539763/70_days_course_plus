"""
关键词检索器 — RAG MVP（无向量库）

基于查询词与文档块的重叠度打分，Day 25+ 可替换为向量检索。

需求：ZL-NA-REQ-019
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.chunker import TextChunk

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+")


@dataclass(frozen=True)
class RetrievalResult:
    """单条检索结果"""

    chunk: TextChunk
    score: float
    matched_tokens: tuple[str, ...] = ()

    def preview(self, max_len: int = 60) -> str:
        text = self.chunk.text.replace("\n", " ")
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


class KeywordRetriever:
    """关键词重叠检索器"""

    def __init__(self, chunks: list[TextChunk] | None = None) -> None:
        self._chunks: list[TextChunk] = list(chunks or [])

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def index(self, chunks: list[TextChunk]) -> None:
        """建立或替换索引"""
        self._chunks = list(chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        """
        按查询词检索最相关文本块。

        Args:
            query: 用户问题
            top_k: 返回条数上限

        Returns:
            按 score 降序的 RetrievalResult 列表
        """
        query = (query or "").strip()
        if not query or not self._chunks:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scored: list[RetrievalResult] = []
        for chunk in self._chunks:
            score, matched = _score_tokens(tokens, chunk.text)
            if score > 0:
                scored.append(
                    RetrievalResult(chunk=chunk, score=score, matched_tokens=matched)
                )

        scored.sort(key=lambda r: (-r.score, -len(r.matched_tokens), r.chunk.index))
        return scored[: max(1, top_k)]


def _tokenize(text: str) -> list[str]:
    """提取中文词段、英文单词与二字片段"""
    tokens: list[str] = []
    seen: set[str] = set()

    for part in _TOKEN_PATTERN.findall(text):
        key = part.lower()
        if key not in seen:
            tokens.append(key)
            seen.add(key)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 0:
            for i in range(len(part) - 1):
                bg = part[i : i + 2]
                if bg not in seen:
                    tokens.append(bg)
                    seen.add(bg)

    return tokens


def _score_tokens(tokens: list[str], text: str) -> tuple[float, tuple[str, ...]]:
    """计算查询 token 在文本中的命中比例"""
    lower = text.lower()
    matched = tuple(t for t in tokens if t in lower)
    if not matched:
        return 0.0, ()
    return len(matched) / len(tokens), matched
