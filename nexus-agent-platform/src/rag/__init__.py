"""NexusAgent RAG 检索模块 — Day 19 入门"""

from rag.chunker import TextChunk, chunk_documents, chunk_text
from rag.context import DocumentIndex, RAGContextService
from rag.embedding import EmbeddingClient, EmbeddingVector, TfidfEmbeddingModel
from rag.embedding_retriever import EmbeddingRetriever
from rag.ingestion import ingest_directory, ingest_upload
from rag.knowledge_store import KnowledgeDocument, KnowledgeStore, get_knowledge_store
from rag.retriever import KeywordRetriever, RetrievalResult
from rag.vector import cosine_similarity, dot_product, normalize_vector, vector_norm

__all__ = [
    "TextChunk",
    "chunk_text",
    "chunk_documents",
    "KeywordRetriever",
    "EmbeddingRetriever",
    "RetrievalResult",
    "DocumentIndex",
    "RAGContextService",
    "KnowledgeStore",
    "KnowledgeDocument",
    "get_knowledge_store",
    "ingest_directory",
    "ingest_upload",
    "EmbeddingClient",
    "EmbeddingVector",
    "TfidfEmbeddingModel",
    "cosine_similarity",
    "dot_product",
    "vector_norm",
    "normalize_vector",
]
