"""
Chroma 向量索引 — 持久化 chunk 向量与元数据

将 Day 20–28 JSON 内嵌的向量索引迁移到 Chroma PersistentClient。
TF-IDF 词表仍保存在 store.json 的 embedding 字段，仅向量落盘 Chroma。

需求：ZL-NA-REQ-029 / ZL-NA-REQ-030
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag.chunker import TextChunk
from rag.embedding import EmbeddingVector

COLLECTION_NAME = "nexus_knowledge"
VECTOR_BACKEND = "chroma"


@dataclass
class ChromaHit:
    """Chroma 查询命中"""

    chunk_id: str
    score: float
    metadata: dict[str, Any]


class ChromaVectorIndex:
    """
    Chroma 持久化向量索引封装。

    典型用法：
        index = ChromaVectorIndex(persist_path)
        index.reset()
        index.upsert_chunks(chunks, vectors)
        hits = index.query(query_vec.values, top_k=3)
    """

    def __init__(
        self,
        persist_path: Path,
        *,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.persist_path = Path(persist_path)
        self.collection_name = collection_name
        self._client: Any = None
        self._collection: Any = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        import chromadb
        from chromadb.config import Settings

        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        return self._client

    def _ensure_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        client = self._ensure_client()
        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def reset(self) -> None:
        """删除并重建 collection（全量 rebuild 时使用）"""
        client = self._ensure_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None
        self._ensure_collection()

    def count(self) -> int:
        return int(self._ensure_collection().count())

    def upsert_chunks(
        self,
        chunks: list[TextChunk],
        vectors: list[EmbeddingVector],
    ) -> int:
        """写入或更新 chunk 向量"""
        if not chunks:
            return 0
        if len(chunks) != len(vectors):
            raise ValueError("chunks 与 vectors 数量不一致")

        collection = self._ensure_collection()
        ids = [c.chunk_id for c in chunks]
        embeddings = [v.values for v in vectors]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "source": c.source,
                "index": c.index,
                "start_char": c.start_char,
                "end_char": c.end_char,
            }
            for c in chunks
        ]
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def delete_by_ids(self, ids: list[str]) -> int:
        """按 chunk_id 删除向量（增量替换旧文档时使用）"""
        if not ids:
            return 0
        collection = self._ensure_collection()
        collection.delete(ids=ids)
        return len(ids)

    def delete_by_source(self, source: str) -> int:
        """按 source 元数据删除某文档的全部向量"""
        if not source:
            return 0
        collection = self._ensure_collection()
        if collection.count() == 0:
            return 0
        try:
            raw = collection.get(where={"source": source}, include=[])
            ids = list(raw.get("ids") or [])
        except Exception:
            ids = []
        if not ids:
            collection.delete(where={"source": source})
            return 0
        collection.delete(ids=ids)
        return len(ids)

    def query(
        self,
        query_vector: list[float],
        *,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> list[ChromaHit]:
        """按查询向量检索，返回按相似度降序的命中"""
        if not query_vector:
            return []
        collection = self._ensure_collection()
        if collection.count() == 0:
            return []

        n_results = max(1, min(top_k, collection.count()))
        raw = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["metadatas", "distances"],
        )

        ids = (raw.get("ids") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]

        hits: list[ChromaHit] = []
        for chunk_id, distance, meta in zip(ids, distances, metadatas):
            score = _distance_to_score(float(distance))
            if score < min_score:
                continue
            hits.append(
                ChromaHit(
                    chunk_id=str(chunk_id),
                    score=score,
                    metadata=dict(meta or {}),
                )
            )
        hits.sort(key=lambda h: (-h.score, h.metadata.get("index", 0)))
        return hits[:top_k]


def _distance_to_score(distance: float) -> float:
    """Chroma cosine distance → 相似度分数（0~1）"""
    return max(0.0, min(1.0, 1.0 - distance))
