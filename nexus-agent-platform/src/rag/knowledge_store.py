"""
知识库存储 — 文档 ingestion、分块索引与 JSON 持久化

将 Day 19–20 的 RAG 管线升级为可写入、可落盘的企业知识库 MVP。

需求：ZL-NA-REQ-025
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.paths import get_path
from rag.chunker import TextChunk, chunk_documents, chunk_text
from rag.chunk_config import DEFAULT_CHUNK_CONFIG, ChunkConfig
from rag.chunk_strategies import chunk_from_parsed
from rag.context import DocumentIndex, RAGContextService
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.chroma_store import VECTOR_BACKEND, ChromaVectorIndex
from tools.doc_reader import DocumentRecord, read_text_file
from tools.parsers.base import ParsedDocument
from utils.json_utils import load_json, save_json
from utils.text_utils import clean_text

STORE_VERSION = "1.1"
PLATFORM_VERSION = "0.29.0"


@dataclass
class KnowledgeDocument:
    """已入库文档元数据"""

    name: str
    ingested_at: str
    size_bytes: int = 0
    chunk_count: int = 0
    format: str = "txt"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ingested_at": self.ingested_at,
            "size_bytes": self.size_bytes,
            "chunk_count": self.chunk_count,
            "format": self.format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeDocument:
        return cls(
            name=str(data.get("name", "")),
            ingested_at=str(data.get("ingested_at", "")),
            size_bytes=int(data.get("size_bytes", 0)),
            chunk_count=int(data.get("chunk_count", 0)),
            format=str(data.get("format", "txt")),
        )


@dataclass
class KnowledgeStore:
    """
    企业知识库 — 分块 + Chroma 向量索引 + JSON 元数据持久化

    典型用法：
        store = KnowledgeStore.load_or_bootstrap()
        store.ingest_text("新产品说明…", filename="notice.txt")
        rag = store.as_rag_service()
    """

    documents: list[KnowledgeDocument] = field(default_factory=list)
    chunks: list[TextChunk] = field(default_factory=list)
    embedding_state: dict[str, Any] = field(default_factory=dict)
    vector_backend: str = VECTOR_BACKEND
    chunk_config: ChunkConfig = field(default_factory=ChunkConfig)
    last_rebuilt_at: str | None = None
    store_path: Path | None = None
    chroma_path: Path | None = None
    _rag_service: RAGContextService | None = field(default=None, repr=False)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def document_count(self) -> int:
        return len(self.documents)

    def as_rag_service(self) -> RAGContextService:
        """构建或返回缓存的 RAGContextService"""
        if self._rag_service is None:
            self._rag_service = self._build_rag_service()
        return self._rag_service

    def invalidate_cache(self) -> None:
        self._rag_service = None

    def get_chunk_config(self) -> ChunkConfig:
        return ChunkConfig.from_dict(self.chunk_config.to_dict())

    def set_chunk_config(self, config: ChunkConfig) -> ChunkConfig:
        config.validate()
        self.chunk_config = ChunkConfig.from_dict(config.to_dict())
        return self.chunk_config

    def ingest_text(
        self,
        content: str,
        *,
        filename: str,
        clean: bool = True,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeDocument:
        """将文本写入知识库并重建索引"""
        cfg = self.get_chunk_config()
        cs = chunk_size if chunk_size is not None else cfg.chunk_size
        ov = overlap if overlap is not None else cfg.overlap
        text = (content or "").strip()
        if not text:
            raise ValueError("文档内容不能为空")
        if not filename.strip():
            raise ValueError("filename 不能为空")

        cleaned = text
        if clean:
            cleaned, _ = clean_text(text)
        doc = DocumentRecord(
            path=Path(filename),
            content=text,
            encoding="utf-8",
            size_bytes=len(text.encode("utf-8")),
            cleaned=cleaned,
        )
        new_chunks = chunk_documents(
            [doc],
            chunk_size=cs,
            overlap=ov,
            use_cleaned=clean,
        )
        self._append_chunks(filename, new_chunks, size_bytes=doc.size_bytes)
        self._rebuild_index()
        return self.documents[-1]

    def ingest_file(
        self,
        path: Path,
        *,
        clean: bool = True,
        chunk_size: int = 200,
        overlap: int = 40,
    ) -> KnowledgeDocument:
        """从磁盘文件 ingestion"""
        content, encoding = read_text_file(path)
        cleaned = content
        if clean:
            cleaned, _ = clean_text(content)
        doc = DocumentRecord(
            path=path,
            content=content,
            encoding=encoding,
            size_bytes=path.stat().st_size,
            cleaned=cleaned,
        )
        new_chunks = chunk_documents(
            [doc],
            chunk_size=chunk_size,
            overlap=overlap,
            use_cleaned=clean,
        )
        self._append_chunks(path.name, new_chunks, size_bytes=doc.size_bytes)
        self._rebuild_index()
        return self.documents[-1]

    def ingest_bytes(
        self,
        data: bytes,
        *,
        filename: str,
        clean: bool = True,
        chunk_strategy: str = "auto",
    ) -> KnowledgeDocument:
        """处理上传二进制 — Day 26 起委托 doc_parser"""
        from tools.doc_parser import parse_bytes

        parsed = parse_bytes(data, filename)
        cfg = self.get_chunk_config()
        return self.ingest_parsed(
            parsed,
            clean=clean,
            chunk_strategy=chunk_strategy if chunk_strategy != "auto" else cfg.strategy,
        )

    def ingest_parsed(
        self,
        parsed: ParsedDocument,
        *,
        clean: bool = True,
        chunk_strategy: str | None = None,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeDocument:
        """将 ParsedDocument 写入知识库"""
        cfg = self.get_chunk_config()
        strategy = chunk_strategy if chunk_strategy is not None else cfg.strategy
        cs = chunk_size if chunk_size is not None else cfg.chunk_size
        ov = overlap if overlap is not None else cfg.overlap
        text = (parsed.plain_text or "").strip()
        if not text:
            raise ValueError("解析结果为空")

        if clean:
            text, _ = clean_text(text)
            parsed.plain_text = text
            for section in parsed.sections:
                section.body, _ = clean_text(section.body)

        new_chunks = chunk_from_parsed(
            parsed,
            strategy=strategy,
            chunk_size=cs,
            overlap=ov,
        )
        size_bytes = len(parsed.plain_text.encode("utf-8"))
        self._append_chunks(
            parsed.filename,
            new_chunks,
            size_bytes=size_bytes,
            doc_format=parsed.format,
        )
        self._rebuild_index()
        return self.documents[-1]

    def save(self, path: Path | None = None) -> Path:
        """持久化到 JSON"""
        target = path or self.store_path or _default_store_path()
        self.store_path = target
        payload = {
            "version": STORE_VERSION,
            "platform_version": PLATFORM_VERSION,
            "documents": [d.to_dict() for d in self.documents],
            "chunks": [_chunk_to_dict(c) for c in self.chunks],
            "embedding": self.embedding_state,
            "vector_backend": self.vector_backend,
            "chunk_config": self.chunk_config.to_dict(),
            "last_rebuilt_at": self.last_rebuilt_at,
        }
        save_json(target, payload)
        return target

    @classmethod
    def load(cls, path: Path) -> KnowledgeStore:
        """从 JSON 加载知识库"""
        raw = load_json(path, default=None)
        if not raw:
            return cls.bootstrap_from_sample_docs(store_path=path)

        store = cls(store_path=path)
        store.documents = [
            KnowledgeDocument.from_dict(d) for d in raw.get("documents", [])
        ]
        store.chunks = [_chunk_from_dict(c) for c in raw.get("chunks", [])]
        store.embedding_state = dict(raw.get("embedding") or {})
        store.vector_backend = str(raw.get("vector_backend") or VECTOR_BACKEND)
        if raw.get("chunk_config"):
            store.chunk_config = ChunkConfig.from_dict(raw["chunk_config"])
        store.last_rebuilt_at = raw.get("last_rebuilt_at")
        store._sync_chroma_from_json()
        store._rag_service = store._build_rag_service()
        return store

    @classmethod
    def load_or_bootstrap(cls, path: Path | None = None) -> KnowledgeStore:
        """加载已有库，不存在则从 sample_docs 引导"""
        target = path or _default_store_path()
        if target.is_file():
            return cls.load(target)
        store = cls.bootstrap_from_sample_docs(store_path=target)
        store.save(target)
        return store

    @classmethod
    def bootstrap_from_sample_docs(cls, *, store_path: Path | None = None) -> KnowledgeStore:
        """用内置 sample_docs 初始化知识库"""
        rag = RAGContextService.from_sample_docs(use_embedding=True)
        store = cls(store_path=store_path)
        now = _utc_now()

        by_source: dict[str, list[TextChunk]] = {}
        for chunk in rag.index.chunks:
            by_source.setdefault(chunk.source, []).append(chunk)

        for source, chunks in sorted(by_source.items()):
            store.documents.append(
                KnowledgeDocument(
                    name=source,
                    ingested_at=now,
                    size_bytes=sum(len(c.text) for c in chunks),
                    chunk_count=len(chunks),
                )
            )
        store.chunks = list(rag.index.chunks)
        retriever = rag.index.retriever
        from rag.embedding_retriever import EmbeddingRetriever

        if isinstance(retriever, EmbeddingRetriever):
            store.embedding_state = retriever._client.model.export_state()
        store._rebuild_index()
        return store

    def status_dict(self) -> dict[str, Any]:
        from tools.doc_parser import supported_formats

        return {
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "documents": [d.to_dict() for d in self.documents],
            "store_path": str(self.store_path) if self.store_path else None,
            "platform_version": PLATFORM_VERSION,
            "supported_formats": supported_formats(),
            "chunk_config": self.chunk_config.to_dict(),
            "last_rebuilt_at": self.last_rebuilt_at,
            "vector_backend": self.vector_backend,
            "chroma_path": str(self._resolve_chroma_path()),
            "chroma_count": self._chroma_index().count() if self.chunks else 0,
        }

    def _append_chunks(
        self,
        filename: str,
        new_chunks: list[TextChunk],
        *,
        size_bytes: int,
        doc_format: str = "txt",
    ) -> None:
        base_index = len(self.chunks)
        reindexed: list[TextChunk] = []
        for i, chunk in enumerate(new_chunks):
            reindexed.append(
                TextChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    source=filename,
                    index=base_index + i,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                )
            )
        self.chunks.extend(reindexed)
        self.documents.append(
            KnowledgeDocument(
                name=filename,
                ingested_at=_utc_now(),
                size_bytes=size_bytes,
                chunk_count=len(reindexed),
                format=doc_format,
            )
        )

    def _resolve_chroma_path(self) -> Path:
        if self.chroma_path is not None:
            return self.chroma_path
        if self.store_path is not None:
            return self.store_path.parent / "chroma"
        return get_path("knowledge_chroma")

    def _chroma_index(self) -> ChromaVectorIndex:
        return ChromaVectorIndex(self._resolve_chroma_path())

    def _sync_chroma_from_json(self) -> None:
        """从 JSON 元数据恢复 Chroma（迁移或冷启动）"""
        if not self.chunks or not self.embedding_state:
            return
        chroma = self._chroma_index()
        if chroma.count() > 0:
            return
        from rag.embedding import EmbeddingClient

        client = EmbeddingClient()
        client.model.load_state(self.embedding_state)
        vectors = client.embed_batch([c.text for c in self.chunks])
        chroma.upsert_chunks(self.chunks, vectors)

    def _rebuild_index(self) -> None:
        from rag.embedding_retriever import EmbeddingRetriever

        if not self.chunks:
            self.embedding_state = {}
            self._chroma_index().reset()
            self.invalidate_cache()
            return

        retriever = EmbeddingRetriever(self.chunks)
        self.embedding_state = retriever._client.model.export_state()
        vectors = retriever._client.embed_batch([c.text for c in self.chunks])
        chroma = self._chroma_index()
        chroma.reset()
        chroma.upsert_chunks(self.chunks, vectors)
        self.invalidate_cache()

    def _build_rag_service(self) -> RAGContextService:
        if not self.chunks:
            return RAGContextService()

        from rag.embedding import EmbeddingClient

        client = EmbeddingClient()
        client.model.load_state(self.embedding_state)
        self._sync_chroma_from_json()
        chroma = self._chroma_index()
        retriever = ChromaEmbeddingRetriever(self.chunks, chroma, client=client)
        index = DocumentIndex(chunks=self.chunks, retriever=retriever)
        return RAGContextService(index)


_store: KnowledgeStore | None = None
_store_lock = threading.Lock()


def get_knowledge_store(*, reload: bool = False) -> KnowledgeStore:
    """全局知识库单例（API 与 factory 共享）"""
    global _store
    with _store_lock:
        if _store is None or reload:
            _store = KnowledgeStore.load_or_bootstrap()
        return _store


def set_knowledge_store(store: KnowledgeStore) -> None:
    """测试注入用"""
    global _store
    with _store_lock:
        _store = store


def _default_store_path() -> Path:
    return get_path("knowledge_store")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _chunk_to_dict(chunk: TextChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "source": chunk.source,
        "index": chunk.index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
    }


def _chunk_from_dict(data: dict[str, Any]) -> TextChunk:
    return TextChunk(
        chunk_id=str(data.get("chunk_id", "")),
        text=str(data.get("text", "")),
        source=str(data.get("source", "")),
        index=int(data.get("index", 0)),
        start_char=int(data.get("start_char", 0)),
        end_char=int(data.get("end_char", 0)),
    )
