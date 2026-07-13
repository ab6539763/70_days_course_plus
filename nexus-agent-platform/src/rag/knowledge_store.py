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
from agent.approval_config import ApprovalConfig
from agent.dify_config import DifyConfig
from agent.mcp_config import McpConfig
from agent.supervisor_config import SupervisorConfig
from agent.executor_config import ExecutorConfig
from agent.graph_config import GraphConfig
from agent.react_config import ReactConfig
from rag.chunker import TextChunk, chunk_documents, chunk_text
from rag.chunk_config import DEFAULT_CHUNK_CONFIG, ChunkConfig
from rag.chunk_strategies import chunk_from_parsed
from rag.context import DocumentIndex, RAGContextService
from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.chroma_store import VECTOR_BACKEND, ChromaVectorIndex
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.expansion_config import ExpansionConfig
from rag.answer_validator import RuleBasedAnswerValidator, ValidationResult
from rag.route_config import RouteConfig
from rag.routing_retriever import RoutingRetriever
from rag.validation_config import ValidationConfig
from rag.hybrid_retriever import HybridRetriever
from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker
from rag.reranking_retriever import RerankingRetriever
from rag.retrieval_config import RetrievalConfig
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever
from tools.doc_reader import DocumentRecord, read_text_file
from tools.parsers.base import ParsedDocument
from utils.json_utils import load_json, save_json
from utils.text_utils import clean_text

STORE_VERSION = "1.1"
PLATFORM_VERSION = "0.45.0"
INDEX_MODE_INCREMENTAL = "incremental"
INDEX_MODE_FULL = "full"


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
    last_incremental_at: str | None = None
    index_mode: str = INDEX_MODE_FULL
    retrieval_config: RetrievalConfig = field(default_factory=RetrievalConfig)
    rerank_config: RerankConfig = field(default_factory=RerankConfig)
    rewrite_config: RewriteConfig = field(default_factory=RewriteConfig)
    citation_config: CitationConfig = field(default_factory=CitationConfig)
    expansion_config: ExpansionConfig = field(default_factory=ExpansionConfig)
    route_config: RouteConfig = field(default_factory=RouteConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    react_config: ReactConfig = field(default_factory=ReactConfig)
    executor_config: ExecutorConfig = field(default_factory=ExecutorConfig)
    graph_config: GraphConfig = field(default_factory=GraphConfig)
    approval_config: ApprovalConfig = field(default_factory=ApprovalConfig)
    supervisor_config: SupervisorConfig = field(default_factory=SupervisorConfig)
    mcp_config: McpConfig = field(default_factory=McpConfig)
    dify_config: DifyConfig = field(default_factory=DifyConfig)
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

    def get_retrieval_config(self) -> RetrievalConfig:
        return RetrievalConfig.from_dict(self.retrieval_config.to_dict())

    def set_retrieval_config(self, config: RetrievalConfig) -> RetrievalConfig:
        config.validate()
        self.retrieval_config = RetrievalConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.retrieval_config

    def get_rerank_config(self) -> RerankConfig:
        return RerankConfig.from_dict(self.rerank_config.to_dict())

    def set_rerank_config(self, config: RerankConfig) -> RerankConfig:
        config.validate()
        self.rerank_config = RerankConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.rerank_config

    def get_rewrite_config(self) -> RewriteConfig:
        return RewriteConfig.from_dict(self.rewrite_config.to_dict())

    def set_rewrite_config(self, config: RewriteConfig) -> RewriteConfig:
        config.validate()
        self.rewrite_config = RewriteConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.rewrite_config

    def get_citation_config(self) -> CitationConfig:
        return CitationConfig.from_dict(self.citation_config.to_dict())

    def set_citation_config(self, config: CitationConfig) -> CitationConfig:
        config.validate()
        self.citation_config = CitationConfig.from_dict(config.to_dict())
        return self.citation_config

    def get_expansion_config(self) -> ExpansionConfig:
        return ExpansionConfig.from_dict(self.expansion_config.to_dict())

    def set_expansion_config(self, config: ExpansionConfig) -> ExpansionConfig:
        config.validate()
        self.expansion_config = ExpansionConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.expansion_config

    def get_route_config(self) -> RouteConfig:
        return RouteConfig.from_dict(self.route_config.to_dict())

    def set_route_config(self, config: RouteConfig) -> RouteConfig:
        config.validate()
        self.route_config = RouteConfig.from_dict(config.to_dict())
        self.invalidate_cache()
        return self.route_config

    def get_validation_config(self) -> ValidationConfig:
        return ValidationConfig.from_dict(self.validation_config.to_dict())

    def set_validation_config(self, config: ValidationConfig) -> ValidationConfig:
        config.validate()
        self.validation_config = ValidationConfig.from_dict(config.to_dict())
        return self.validation_config

    def get_react_config(self) -> ReactConfig:
        return ReactConfig.from_dict(self.react_config.to_dict())

    def set_react_config(self, config: ReactConfig) -> ReactConfig:
        config.validate()
        self.react_config = ReactConfig.from_dict(config.to_dict())
        return self.react_config

    def get_executor_config(self) -> ExecutorConfig:
        return ExecutorConfig.from_dict(self.executor_config.to_dict())

    def set_executor_config(self, config: ExecutorConfig) -> ExecutorConfig:
        config.validate()
        self.executor_config = ExecutorConfig.from_dict(config.to_dict())
        return self.executor_config

    def get_graph_config(self) -> GraphConfig:
        return GraphConfig.from_dict(self.graph_config.to_dict())

    def set_graph_config(self, config: GraphConfig) -> GraphConfig:
        config.validate()
        self.graph_config = GraphConfig.from_dict(config.to_dict())
        return self.graph_config

    def get_approval_config(self) -> ApprovalConfig:
        return ApprovalConfig.from_dict(self.approval_config.to_dict())

    def set_approval_config(self, config: ApprovalConfig) -> ApprovalConfig:
        config.validate()
        self.approval_config = ApprovalConfig.from_dict(config.to_dict())
        return self.approval_config

    def get_supervisor_config(self) -> SupervisorConfig:
        return SupervisorConfig.from_dict(self.supervisor_config.to_dict())

    def set_supervisor_config(self, config: SupervisorConfig) -> SupervisorConfig:
        config.validate()
        self.supervisor_config = SupervisorConfig.from_dict(config.to_dict())
        return self.supervisor_config

    def get_mcp_config(self) -> McpConfig:
        return McpConfig.from_dict(self.mcp_config.to_dict())

    def set_mcp_config(self, config: McpConfig) -> McpConfig:
        config.validate()
        self.mcp_config = McpConfig.from_dict(config.to_dict())
        return self.mcp_config

    def get_dify_config(self) -> DifyConfig:
        return DifyConfig.from_dict(self.dify_config.to_dict())

    def set_dify_config(self, config: DifyConfig) -> DifyConfig:
        config.validate()
        self.dify_config = DifyConfig.from_dict(config.to_dict())
        return self.dify_config

    def validate_answer(
        self,
        query: str,
        reply: str,
        citations: list[dict[str, Any]],
    ) -> ValidationResult | None:
        """按当前 validation_config 校验 reply 与 citations 一致性"""
        cfg = self.get_validation_config()
        if not cfg.enabled:
            return None
        validator = RuleBasedAnswerValidator(config=cfg)
        return validator.validate(query, reply, citations)

    def fetch_citations(self, query: str) -> dict[str, Any]:
        """按当前 citation_config 检索并返回引用包 dict"""
        cfg = self.get_citation_config()
        if not cfg.enabled:
            return {
                "query": query.strip(),
                "citations": [],
                "rewrite": None,
                "expansion": None,
                "route": None,
            }
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(query, config=cfg)
        return bundle.to_dict()

    def fetch_citations_retry(self, query: str, *, attempt: int = 1) -> dict[str, Any]:
        """Self-RAG 重试 — 强制 rag_wide 并放大 citation pool"""
        from rag.citation_config import CitationConfig
        from rag.route_config import INTENT_RAG_WIDE

        cfg = self.get_citation_config()
        if not cfg.enabled:
            return self.fetch_citations(query)

        boosted = CitationConfig.from_dict(
            {
                **cfg.to_dict(),
                "max_citations": min(100, max(cfg.max_citations, 20) + attempt * 10),
            }
        )
        rag = self.as_rag_service()
        bundle = rag.retrieve_citation_bundle(
            query,
            config=boosted,
            intent_override=INTENT_RAG_WIDE,
        )
        data = bundle.to_dict()
        data["retry_attempt"] = attempt
        return data

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
        incremental: bool = True,
    ) -> KnowledgeDocument:
        """处理上传二进制 — Day 26 起委托 doc_parser"""
        from tools.doc_parser import parse_bytes

        parsed = parse_bytes(data, filename)
        cfg = self.get_chunk_config()
        return self.ingest_parsed(
            parsed,
            clean=clean,
            chunk_strategy=chunk_strategy if chunk_strategy != "auto" else cfg.strategy,
            incremental=incremental,
        )

    def ingest_parsed(
        self,
        parsed: ParsedDocument,
        *,
        clean: bool = True,
        chunk_strategy: str | None = None,
        chunk_size: int | None = None,
        overlap: int | None = None,
        incremental: bool = False,
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

        if incremental:
            removed = self._remove_document_by_source(parsed.filename)
            self._append_chunks(
                parsed.filename,
                new_chunks,
                size_bytes=size_bytes,
                doc_format=parsed.format,
            )
            self._incremental_index(new_chunks, replaced_count=len(removed))
        else:
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
            "last_incremental_at": self.last_incremental_at,
            "index_mode": self.index_mode,
            "retrieval_config": self.retrieval_config.to_dict(),
            "rerank_config": self.rerank_config.to_dict(),
            "rewrite_config": self.rewrite_config.to_dict(),
            "citation_config": self.citation_config.to_dict(),
            "expansion_config": self.expansion_config.to_dict(),
            "route_config": self.route_config.to_dict(),
            "validation_config": self.validation_config.to_dict(),
            "react_config": self.react_config.to_dict(),
            "executor_config": self.executor_config.to_dict(),
            "graph_config": self.graph_config.to_dict(),
            "approval_config": self.approval_config.to_dict(),
            "supervisor_config": self.supervisor_config.to_dict(),
            "mcp_config": self.mcp_config.to_dict(),
            "dify_config": self.dify_config.to_dict(),
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
        store.last_incremental_at = raw.get("last_incremental_at")
        store.index_mode = str(raw.get("index_mode") or INDEX_MODE_FULL)
        if raw.get("retrieval_config"):
            store.retrieval_config = RetrievalConfig.from_dict(raw["retrieval_config"])
        if raw.get("rerank_config"):
            store.rerank_config = RerankConfig.from_dict(raw["rerank_config"])
        if raw.get("rewrite_config"):
            store.rewrite_config = RewriteConfig.from_dict(raw["rewrite_config"])
        if raw.get("citation_config"):
            store.citation_config = CitationConfig.from_dict(raw["citation_config"])
        if raw.get("expansion_config"):
            store.expansion_config = ExpansionConfig.from_dict(raw["expansion_config"])
        if raw.get("route_config"):
            store.route_config = RouteConfig.from_dict(raw["route_config"])
        if raw.get("validation_config"):
            store.validation_config = ValidationConfig.from_dict(raw["validation_config"])
        if raw.get("react_config"):
            store.react_config = ReactConfig.from_dict(raw["react_config"])
        if raw.get("executor_config"):
            store.executor_config = ExecutorConfig.from_dict(raw["executor_config"])
        if raw.get("graph_config"):
            store.graph_config = GraphConfig.from_dict(raw["graph_config"])
        if raw.get("approval_config"):
            store.approval_config = ApprovalConfig.from_dict(raw["approval_config"])
        if raw.get("supervisor_config"):
            store.supervisor_config = SupervisorConfig.from_dict(raw["supervisor_config"])
        if raw.get("mcp_config"):
            store.mcp_config = McpConfig.from_dict(raw["mcp_config"])
        if raw.get("dify_config"):
            store.dify_config = DifyConfig.from_dict(raw["dify_config"])
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
            "last_incremental_at": self.last_incremental_at,
            "index_mode": self.index_mode,
            "retrieval_config": self.retrieval_config.to_dict(),
            "rerank_config": self.rerank_config.to_dict(),
            "rewrite_config": self.rewrite_config.to_dict(),
            "citation_config": self.citation_config.to_dict(),
            "expansion_config": self.expansion_config.to_dict(),
            "route_config": self.route_config.to_dict(),
            "validation_config": self.validation_config.to_dict(),
            "react_config": self.react_config.to_dict(),
            "executor_config": self.executor_config.to_dict(),
            "graph_config": self.graph_config.to_dict(),
            "approval_config": self.approval_config.to_dict(),
            "supervisor_config": self.supervisor_config.to_dict(),
            "mcp_config": self.mcp_config.to_dict(),
            "dify_config": self.dify_config.to_dict(),
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

    def _remove_document_by_source(self, filename: str) -> list[str]:
        """移除同名文档及其 chunks，并从 Chroma 删除旧向量"""
        removed_ids = [c.chunk_id for c in self.chunks if c.source == filename]
        if not removed_ids:
            return []

        self._chroma_index().delete_by_ids(removed_ids)
        self.documents = [d for d in self.documents if d.name != filename]
        self.chunks = [c for c in self.chunks if c.source != filename]
        self.chunks = [
            TextChunk(
                chunk_id=c.chunk_id,
                text=c.text,
                source=c.source,
                index=i,
                start_char=c.start_char,
                end_char=c.end_char,
            )
            for i, c in enumerate(self.chunks)
        ]
        return removed_ids

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
        self.index_mode = INDEX_MODE_FULL
        self.invalidate_cache()

    def _incremental_index(
        self,
        affected_chunks: list[TextChunk],
        *,
        replaced_count: int = 0,
    ) -> bool:
        """
        增量更新 Chroma：不 reset collection，仅 upsert 受影响 chunk。

        若 TF-IDF 词表扩张，则回退为全量 upsert（仍不 reset）。
        返回是否发生词表扩张。
        """
        from rag.embedding_retriever import EmbeddingRetriever

        if not self.chunks:
            self.embedding_state = {}
            self._chroma_index().reset()
            self.last_incremental_at = _utc_now()
            self.index_mode = INDEX_MODE_INCREMENTAL
            self.invalidate_cache()
            return False

        old_vocab = dict(self.embedding_state.get("vocab") or {})
        retriever = EmbeddingRetriever(self.chunks)
        self.embedding_state = retriever._client.model.export_state()
        new_vocab = dict(self.embedding_state.get("vocab") or {})
        vocab_expanded = len(new_vocab) > len(old_vocab) and bool(old_vocab)

        if vocab_expanded:
            affected_chunks = list(self.chunks)

        client = retriever._client
        vectors = client.embed_batch([c.text for c in affected_chunks])
        chroma = self._chroma_index()
        if vocab_expanded:
            # TF-IDF 维度变化时 Chroma collection 须重建
            chroma.reset()
        chroma.upsert_chunks(affected_chunks, vectors)
        self.last_incremental_at = _utc_now()
        self.index_mode = INDEX_MODE_INCREMENTAL
        self.invalidate_cache()
        return vocab_expanded

    def _build_rag_service(self) -> RAGContextService:
        if not self.chunks:
            return RAGContextService()

        from rag.embedding import EmbeddingClient
        from rag.retriever import KeywordRetriever

        client = EmbeddingClient()
        client.model.load_state(self.embedding_state)
        self._sync_chroma_from_json()
        chroma = self._chroma_index()
        vector = ChromaEmbeddingRetriever(self.chunks, chroma, client=client)
        keyword = KeywordRetriever(self.chunks)
        cfg = self.get_retrieval_config()
        hybrid = HybridRetriever(self.chunks, keyword, vector, config=cfg)
        rerank_cfg = self.get_rerank_config()
        reranking = RerankingRetriever(
            hybrid,
            reranker=MockCrossEncoderReranker(),
            config=rerank_cfg,
        )
        rewrite_cfg = self.get_rewrite_config()
        rewriting = RewritingRetriever(reranking, config=rewrite_cfg)
        expansion_cfg = self.get_expansion_config()
        expanding = ExpandingRetriever(rewriting, config=expansion_cfg)
        route_cfg = self.get_route_config()
        retriever = RoutingRetriever(expanding, config=route_cfg)
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
