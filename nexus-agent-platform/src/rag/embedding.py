"""
TF-IDF Embedding 模型 — 离线语义向量 MVP

将文本映射为固定维度稀疏向量，用余弦相似度衡量语义相近度。
生产环境可替换为 Embedding API，接口保持一致。

需求：ZL-NA-REQ-020
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rag.synonyms import expand_tokens, tokenize
from rag.vector import cosine_similarity


@dataclass
class EmbeddingVector:
    """文本的向量表示"""

    text: str
    values: list[float] = field(default_factory=list)
    dimension: int = 0

    def similarity_to(self, other: EmbeddingVector) -> float:
        return cosine_similarity(self.values, other.values)


class TfidfEmbeddingModel:
    """
    基于 TF-IDF 的文本向量化模型。

    在 sample_docs 规模下完全离线，CI 友好。
    """

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}
        self._idf: list[float] = []
        self._fitted = False

    @property
    def dimension(self) -> int:
        return len(self._vocab)

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit(self, texts: list[str]) -> TfidfEmbeddingModel:
        """在语料上建立词表与 IDF"""
        doc_tokens: list[list[str]] = []
        df: dict[str, int] = {}

        for text in texts:
            tokens = expand_tokens(tokenize(text), text)
            doc_tokens.append(tokens)
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1

        self._vocab = {term: idx for idx, term in enumerate(sorted(df))}
        n_docs = max(len(texts), 1)
        self._idf = [0.0] * len(self._vocab)
        for term, idx in self._vocab.items():
            self._idf[idx] = math.log((1 + n_docs) / (1 + df[term])) + 1.0

        self._fitted = True
        return self

    def embed(self, text: str) -> EmbeddingVector:
        """将单条文本转为向量"""
        if not self._fitted:
            raise RuntimeError("请先调用 fit() 在语料上训练模型")

        tokens = expand_tokens(tokenize(text), text)
        vec = [0.0] * len(self._vocab)
        if not tokens:
            return EmbeddingVector(text=text, values=vec, dimension=len(vec))

        tf: dict[str, int] = {}
        for t in tokens:
            if t in self._vocab:
                tf[t] = tf.get(t, 0) + 1

        for term, count in tf.items():
            idx = self._vocab[term]
            vec[idx] = (count / len(tokens)) * self._idf[idx]

        return EmbeddingVector(text=text, values=vec, dimension=len(vec))

    def similarity(self, text_a: str, text_b: str) -> float:
        """两条文本的余弦相似度"""
        return self.embed(text_a).similarity_to(self.embed(text_b))

    def export_state(self) -> dict:
        """导出词表与 IDF，供 KnowledgeStore 持久化"""
        return {
            "vocab": self._vocab,
            "idf": self._idf,
            "fitted": self._fitted,
        }

    def load_state(self, state: dict) -> None:
        """从持久化状态恢复模型"""
        self._vocab = dict(state.get("vocab") or {})
        self._idf = list(state.get("idf") or [])
        self._fitted = bool(state.get("fitted")) and bool(self._vocab)


class EmbeddingClient:
    """
    Embedding 客户端门面 — 封装模型与批量编码。

    Day 25+ 可增加 HTTP API 实现。
    """

    def __init__(self, model: TfidfEmbeddingModel | None = None) -> None:
        self.model = model or TfidfEmbeddingModel()

    def fit_corpus(self, texts: list[str]) -> None:
        self.model.fit(texts)

    def embed(self, text: str) -> EmbeddingVector:
        return self.model.embed(text)

    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]:
        return [self.embed(t) for t in texts]

    def similarity(self, text_a: str, text_b: str) -> float:
        return self.model.similarity(text_a, text_b)
