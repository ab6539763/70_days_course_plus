# Day 29 精读：chroma_store.py 与 chroma_retriever.py

**需求**：ZL-NA-REQ-029 | **建议学时**：90 分钟  
本课全文嵌入仓库**真实源码**，请对照 IDE 单行调试。

---

## 一、模块职责

`chroma_store.py` 隔离 `chromadb` 第三方 API，向上提供稳定的 `ChromaVectorIndex`。`chroma_retriever.py` 实现与 `EmbeddingRetriever` 相同的检索端口，供 `DocumentIndex` 无感切换。

---

## 二、chroma_store.py 完整源码

```python
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
```


---

## 三、逐段讲解

### 3.1 延迟 import（L54–65）

```python
def _ensure_client(self) -> Any:
    if self._client is not None:
        return self._client
    import chromadb
```

**原因**：未安装 chromadb 时，仅 import `knowledge_store` 不立刻失败；真正访问 Chroma 才报错。测试可 mock。

### 3.2 reset()（L77–85）

`delete_collection` 吞掉「不存在」异常，然后 `_collection = None` 再 `_ensure_collection()`。**必须**重建句柄，否则 upsert 到已删 collection。

### 3.3 upsert_chunks（L90–120）

- `ids` 使用业务主键 `chunk_id`，保证跨 rebuild 可追踪（同内容同 id 策略由 chunker 决定）  
- `documents` 存原文方便 `chromadb` CLI 调试  
- `metadatas` 的 `source` 供 Day 30 `delete_by_source`  

### 3.4 query（L148–186）

`n_results = max(1, min(top_k, collection.count()))` 避免空库或 top_k 过大报错。排序：`(-score, index)` 稳定 tie-break。

### 3.5 delete_by_ids / delete_by_source（L122–146）

Day 29 已实现，Day 30 增量替换同名文档时调用。`delete_by_source` 先 `get(where=...)` 再 `delete(ids=...)`，兼容不同 chromadb 版本。

---

## 四、chroma_retriever.py 完整源码

```python
"""
Chroma 向量检索器 — 与 EmbeddingRetriever 接口一致

需求：ZL-NA-REQ-029
"""

from __future__ import annotations

from rag.chunker import TextChunk
from rag.chroma_store import ChromaVectorIndex
from rag.embedding import EmbeddingClient
from rag.embedding_retriever import _overlap_terms
from rag.retriever import RetrievalResult


class ChromaEmbeddingRetriever:
    """基于 Chroma 持久化索引的向量检索器"""

    def __init__(
        self,
        chunks: list[TextChunk],
        chroma_index: ChromaVectorIndex,
        *,
        client: EmbeddingClient | None = None,
        min_score: float = 0.05,
    ) -> None:
        self._chunks_by_id = {c.chunk_id: c for c in chunks}
        self._chroma = chroma_index
        self._client = client or EmbeddingClient()
        self._min_score = min_score

    @property
    def chunk_count(self) -> int:
        return self._chroma.count()

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievalResult]:
        query = (query or "").strip()
        if not query or not self._chunks_by_id:
            return []

        if not self._client.model.is_fitted:
            return []

        query_vec = self._client.embed(query)
        hits = self._chroma.query(
            query_vec.values,
            top_k=top_k,
            min_score=self._min_score,
        )

        scored: list[RetrievalResult] = []
        for hit in hits:
            chunk = self._chunks_by_id.get(hit.chunk_id)
            if chunk is None:
                continue
            matched = _overlap_terms(query, chunk.text)
            scored.append(
                RetrievalResult(
                    chunk=chunk,
                    score=hit.score,
                    matched_tokens=matched,
                )
            )

        if not scored:
            return []
        return scored[: max(1, top_k)]
```


### 4.1 _chunks_by_id 字典

O(1) 由 `chunk_id` 取 `TextChunk`。若 Chroma 命中 id 在 JSON 中不存在（不一致），**跳过**该 hit，防止脏数据。

### 4.2 model.is_fitted 检查

词表未加载时返回 `[]`，与 `EmbeddingRetriever` 一致。

### 4.3 _overlap_terms

保留 matched_tokens 供前端高亮，与内存 retriever 行为一致。

---

## 五、与 KnowledgeStore 的接点

```python
# knowledge_store._rebuild_index 核心四行
retriever = EmbeddingRetriever(self.chunks)
self.embedding_state = retriever._client.model.export_state()
vectors = retriever._client.embed_batch([c.text for c in self.chunks])
chroma.reset()
chroma.upsert_chunks(self.chunks, vectors)
```

---

## 六、调试练习

1. 在 `upsert_chunks` 打日志，打印 `len(ids)` 与 `chroma.count()`  
2. 修改 `min_score=0.99`，观察 search 返回空列表  
3. 对比 `EmbeddingRetriever` 与 `ChromaEmbeddingRetriever` 同一 query 的 top-3  

---

## 七、自检问题

1. 为何 `upsert` 而不是 `add`？  
2. `ChromaHit` 与 `RetrievalResult` 为何分两层？  
3. 若 `distance` 为 NaN 会怎样？（`_distance_to_score` clamp 能否处理？）

---

## 十二、chroma_store.py 逐行精读表

| 行号区间 | 代码职责 | 讲师点评 |
|----------|----------|----------|
| L1–8 | 模块 docstring | 标明 REQ-029/030 双需求：删除 API 为 Day 30 预埋 |
| L19–20 | COLLECTION_NAME / VECTOR_BACKEND | 常量供测试与 status 断言 |
| L23–29 | ChromaHit dataclass | 比 RetrievalResult 更贴近 Chroma 原生返回 |
| L32–52 | __init__ 延迟连接 | persist_path 可测试注入 |
| L54–65 | _ensure_client | 延迟 import chromadb；mkdir；关遥测 |
| L67–75 | _ensure_collection | cosine 空间在此固定，全库一致 |
| L77–85 | reset | 全量 rebuild 入口；吞 delete 异常防首次空库报错 |
| L87–88 | count | 运维健康检查核心 |
| L90–120 | upsert_chunks | 四列表对齐；ValueError Guard |
| L122–128 | delete_by_ids | Day 30 同名替换删旧 chunk |
| L130–146 | delete_by_source | metadata 过滤；兼容多版本 API |
| L148–186 | query | n_results 边界；min_score 过滤；排序稳定 |
| L189–191 | _distance_to_score | 纯函数，便于单测 |

建议学员用 IDE「跳转定义」对照本表，每行加断点观察一次 query 全流程。

---

## 十三、chroma_retriever 与 DocumentIndex 契约

`DocumentIndex.retrieve` 不关心向量来自内存还是 Chroma，仅调用 `self._retriever.search`。因此 Day 29 切换 retriever 后，`RAGContextService` 与 `api/chat` **零修改**。这是端口适配器模式的典型案例。

---

## 十四、课后重构题（不提交）

若将 `ChromaVectorIndex` 改为抽象基类 `VectorIndexBase`，列出子类需实现的 6 个方法。思考：Day 31 混合检索是否需扩展接口？

---

## 八、knowledge_store.py 集成节选（真实源码）

### 8.1 模块头与常量

```python
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
from rag.citation_config import CitationConfig
from rag.expanding_retriever import ExpandingRetriever
from rag.expansion_config import ExpansionConfig
from rag.route_config import RouteConfig
from rag.routing_retriever import RoutingRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.rerank_config import RerankConfig
from rag.reranker import MockCrossEncoderReranker
from rag.reranking_retriever import RerankingRetriever
from rag.retrieval_config import RetrievalConfig
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever
```


### 8.2 ingest_parsed 非增量分支（Day 29 upload 仍走此路径）

```python
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
```


### 8.3 load 与 _sync 调用点

```python
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
        store._sync_chroma_from_json()
        store._rag_service = store._build_rag_service()
        return store

    @classmethod
```


### 8.4 _build_rag_service 完整实现

```python
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
```


---

## 九、test_chroma_index.py 全文走读

```python
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
```


### 9.1 测试夹具 _store

每个测试用 `tmp_path` 隔离 `store.json` 与 `chroma/`，避免污染开发者默认 `data/knowledge/`。`bootstrap_from_sample_docs` 保证有 sample 块可检索。

### 9.2 test_load_restores_chroma_from_json

证明「仅删 chroma 不删 JSON」时 load 能恢复 count。这是运维事故最常见场景。

### 9.3 test_empty_store_clears_chroma

空库必须 `chroma.count()==0`，防止脏向量残留影响「空库」语义。

---

## 十、与 EmbeddingRetriever 的接口契约

| 方法 | EmbeddingRetriever | ChromaEmbeddingRetriever |
|------|-------------------|------------------------|
| search(query, top_k=3) | ✅ | ✅ |
| chunk_count | len(chunks) | chroma.count() |
| 依赖 | 内存向量列表 | Chroma + chunks 字典 |

`DocumentIndex` 只依赖 `search` 返回 `RetrievalResult`，故切换 retriever 不改上层 RAG 代码。

---

## 十一、延伸阅读代码路径

- `rag/embedding_retriever.py` — 内存检索基准  
- `rag/context.py` — DocumentIndex.retrieve  
- `core/paths.py` — knowledge_chroma 路径注册  
- `api/schemas.py` — KnowledgeStatusResponse 字段定义
