"""
相似问题匹配服务 — FAQ 去重与智能路由

基于 Embedding 余弦相似度，将用户问题映射到标准 FAQ。

需求：ZL-NA-REQ-020
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.embedding import EmbeddingClient, TfidfEmbeddingModel


@dataclass(frozen=True)
class FaqEntry:
    """FAQ 条目"""

    question: str
    answer: str
    category: str = "general"


@dataclass
class FaqMatch:
    """匹配结果"""

    entry: FaqEntry
    score: float
    user_question: str

    def summary(self) -> str:
        return (
            f"匹配 FAQ「{self.entry.question}」| "
            f"相似度={self.score:.0%} | 分类={self.entry.category}"
        )


# 内置示例 FAQ（智链科技理财场景）
DEFAULT_FAQ: tuple[FaqEntry, ...] = (
    FaqEntry("年化收益率是多少？", "请参考产品说明书，收益率以公告为准。", "product"),
    FaqEntry("投资有风险吗？", "投资有风险，入市需谨慎。请阅读风险揭示书。", "risk"),
    FaqEntry("如何联系客服？", "客服热线 400-888-9999，工作日 9:00-18:00。", "service"),
    FaqEntry("可以上传 PDF 文档吗？", "在控制台「知识库」-「上传文档」即可。", "platform"),
    FaqEntry("什么是内部资料？", "标注【内部资料】的内容禁止外传。", "compliance"),
)


class SimilarQuestionMatcher:
    """
    相似问题匹配器

    典型用法：
        matcher = SimilarQuestionMatcher()
        match = matcher.match("投资回报率怎么算？")
        if match:
            print(match.entry.answer)
    """

    def __init__(
        self,
        entries: tuple[FaqEntry, ...] | list[FaqEntry] | None = None,
        *,
        threshold: float = 0.32,
        client: EmbeddingClient | None = None,
    ) -> None:
        self.entries = list(entries or DEFAULT_FAQ)
        self.threshold = threshold
        self._client = client or EmbeddingClient()
        self._vectors = []
        self._reindex()

    def _reindex(self) -> None:
        questions = [e.question for e in self.entries]
        self._client.fit_corpus(questions)
        self._vectors = self._client.embed_batch(questions)

    def match(self, user_question: str) -> FaqMatch | None:
        """返回最佳匹配，低于阈值则 None"""
        user_question = (user_question or "").strip()
        if not user_question or not self.entries:
            return None

        query_vec = self._client.embed(user_question)
        best: FaqMatch | None = None

        for entry, vec in zip(self.entries, self._vectors):
            score = query_vec.similarity_to(vec)
            if score >= self.threshold and (best is None or score > best.score):
                best = FaqMatch(entry=entry, score=score, user_question=user_question)

        return best

    def match_all(self, user_question: str, *, top_k: int = 3) -> list[FaqMatch]:
        """返回 top_k 候选"""
        user_question = (user_question or "").strip()
        if not user_question:
            return []

        query_vec = self._client.embed(user_question)
        matches: list[FaqMatch] = []

        for entry, vec in zip(self.entries, self._vectors):
            score = query_vec.similarity_to(vec)
            if score >= self.threshold:
                matches.append(
                    FaqMatch(entry=entry, score=score, user_question=user_question)
                )

        matches.sort(key=lambda m: -m.score)
        return matches[:top_k]
