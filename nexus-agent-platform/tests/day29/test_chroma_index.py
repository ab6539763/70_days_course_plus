"""Day 29 Chroma 向量库测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chroma_retriever import ChromaEmbeddingRetriever
from rag.chroma_store import VECTOR_BACKEND, ChromaVectorIndex
from rag.embedding import EmbeddingClient
from rag.embedding_retriever import EmbeddingRetriever
from rag.knowledge_rebuild import rebuild_store
from rag.knowledge_store import KnowledgeStore


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def test_chroma_index_upsert_and_query(tmp_path):
    store = _store(tmp_path)
    chroma = ChromaVectorIndex(tmp_path / "chroma2")
    client = EmbeddingClient()
    client.model.load_state(store.embedding_state)
    vectors = client.embed_batch([c.text for c in store.chunks])
    chroma.reset()
    count = chroma.upsert_chunks(store.chunks, vectors)
    assert count == len(store.chunks)
    assert chroma.count() == len(store.chunks)

    query_vec = client.embed("年化收益率")
    hits = chroma.query(query_vec.values, top_k=2)
    assert len(hits) >= 1
    assert hits[0].score > 0


def test_chroma_retriever_search(tmp_path):
    store = _store(tmp_path)
    chroma = ChromaVectorIndex(store._resolve_chroma_path())
    client = EmbeddingClient()
    client.model.load_state(store.embedding_state)
    retriever = ChromaEmbeddingRetriever(store.chunks, chroma, client=client)
    results = retriever.search("年化收益", top_k=2)
    assert len(results) >= 1
    assert results[0].score > 0


def test_knowledge_store_uses_chroma_backend(tmp_path):
    store = _store(tmp_path)
    status = store.status_dict()
    assert status["vector_backend"] == VECTOR_BACKEND
    assert status["chroma_count"] == store.chunk_count


def test_bootstrap_populates_chroma(tmp_path):
    path = tmp_path / "boot.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma_boot"
    store._rebuild_index()
    store.save(path)
    assert store._chroma_index().count() == store.chunk_count


def test_load_restores_chroma_from_json(tmp_path):
    store = _store(tmp_path)
    chroma_path = store._resolve_chroma_path()
    loaded = KnowledgeStore.load(store.store_path)
    loaded.chroma_path = chroma_path
    assert loaded._chroma_index().count() == loaded.chunk_count


def test_rebuild_resets_chroma_collection(tmp_path):
    store = _store(tmp_path)
    before = store._chroma_index().count()
    report = rebuild_store(store)
    after = store._chroma_index().count()
    assert after == report.chunks_after
    assert after == store.chunk_count
    assert before == store.chunk_count or before > 0


def test_rag_service_retrieves_via_chroma(tmp_path):
    store = _store(tmp_path)
    rag = store.as_rag_service()
    ctx = rag.retrieve_context("年化收益率")
    assert "年化" in ctx or "收益" in ctx or "片段" in ctx


def test_save_includes_vector_backend(tmp_path):
    store = _store(tmp_path)
    from utils.json_utils import load_json

    raw = load_json(store.store_path)
    assert raw["vector_backend"] == VECTOR_BACKEND
    assert raw["version"] == "1.1"


def test_chroma_matches_in_memory_retriever_top1(tmp_path):
    store = _store(tmp_path)
    query = "年化收益率是多少"
    mem = EmbeddingRetriever(store.chunks)
    chroma = store._chroma_index()
    client = EmbeddingClient()
    client.model.load_state(store.embedding_state)
    chroma_r = ChromaEmbeddingRetriever(store.chunks, chroma, client=client)

    mem_top = mem.search(query, top_k=1)
    chroma_top = chroma_r.search(query, top_k=1)
    assert mem_top and chroma_top
    assert mem_top[0].chunk.chunk_id == chroma_top[0].chunk.chunk_id


def test_empty_store_clears_chroma(tmp_path):
    path = tmp_path / "empty.json"
    store = KnowledgeStore(store_path=path, chroma_path=tmp_path / "chroma_empty")
    store._rebuild_index()
    assert store._chroma_index().count() == 0
