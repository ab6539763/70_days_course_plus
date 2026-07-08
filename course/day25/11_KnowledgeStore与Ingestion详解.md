# KnowledgeStore 与 Ingestion 详解

**需求**：ZL-NA-REQ-025 | **版本**：0.25.0

## 1. 从只读到可写

Day 19–20：`RAGContextService.from_sample_docs()` 在内存构建索引，进程结束即失。  
Day 25：`KnowledgeStore` 把 chunks + embedding state 序列化，重启可 `load`。

## 2. bootstrap_from_sample_docs 算法

1. 调用 `RAGContextService.from_sample_docs(use_embedding=True)`  
2. 按 `chunk.source` 分组统计 `KnowledgeDocument`  
3. 复制 chunks 列表  
4. 从 `EmbeddingRetriever` export embedding_state  
5. `_rebuild_index()` 确保一致性  

保证与 Day 24 演示 FAQ 行为一致，降低回归风险。

## 3. ingest_text 逐步

```python
def ingest_text(self, content, *, filename, clean=True, chunk_size=None, overlap=None):
    cfg = self.get_chunk_config()
    cs = chunk_size if chunk_size is not None else cfg.chunk_size
    text = (content or "").strip()
    if not text:
        raise ValueError("文档内容不能为空")
    cleaned = clean_text(text) if clean else text
    doc = DocumentRecord(path=Path(filename), content=text, ...)
    new_chunks = chunk_documents([doc], chunk_size=cs, overlap=ov, use_cleaned=clean)
    self._append_chunks(filename, new_chunks, size_bytes=...)
    self._rebuild_index()
    return self.documents[-1]
```


## 4. ingest_upload 路径

```python
"""
文档 ingestion 流水线 — 读取、解析、清洗、分块、入库

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import NexusError, StorageError
from rag.knowledge_store import KnowledgeDocument, KnowledgeStore, get_knowledge_store
from tools.doc_parser import detect_format, parse_bytes, supported_formats
from tools.doc_reader import read_documents


def ingest_directory(
    directory: Path,
    *,
    pattern: str = "*.txt",
    clean: bool = True,
    store: KnowledgeStore | None = None,
) -> list[KnowledgeDocument]:
    """批量将目录下文本文件写入知识库"""
    kb = store or get_knowledge_store()
    docs = read_documents(directory, pattern=pattern, clean=clean)
    results: list[KnowledgeDocument] = []
    for doc in docs:
        content = doc.cleaned if clean and doc.cleaned else doc.content
        meta = kb.ingest_text(content, filename=doc.name, clean=False)
        results.append(meta)
    kb.save()
    return results


def ingest_upload(
    data: bytes,
    filename: str,
    *,
    store: KnowledgeStore | None = None,
    uploads_dir: Path | None = None,
    chunk_strategy: str = "auto",
) -> KnowledgeDocument:
    """处理 API 上传：解析 → 落盘 → 入库"""
    from core.paths import get_path

    kb = store or get_knowledge_store()
    target_dir = uploads_dir or get_path("knowledge_uploads")
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    try:
        detect_format(safe_name)
    except NexusError as exc:
        raise ValueError(exc.message) from exc

    dest = target_dir / safe_name
    dest.write_bytes(data)
    meta = kb.ingest_bytes(
        data,
        filename=safe_name,
        chunk_strategy=chunk_strategy,
    )
    kb.save()
    return meta


__all__ = ["ingest_directory", "ingest_upload", "supported_formats"]
```


## 5. 单例与测试隔离

生产：`get_knowledge_store()` 懒加载。  
测试：`set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs(store_path=tmp))` 避免污染全局 JSON。

## 6. 性能注记

Day 25 每次 ingest 全量 `_rebuild_index`，复杂度 O(n)。sample 规模可接受；Day 29 增量 Chroma。

详解完。

---

## 附录：chunk_documents 与 KnowledgeStore 边界

KnowledgeStore 不实现分块算法，只调用 `chunk_documents` / Day 26 `chunk_from_parsed`。解析层在 `tools/`，分块策略在 `rag/chunk_strategies.py`（Day 26），索引在 store。三层分离是 Phase 3 架构红线。

## 附录：错误处理链

ingest_text ValueError → API 422；StorageError → 500；UnicodeDecodeError → 400。学员在 17_ 速查手写错误矩阵。



---

## 附录：_append_chunks 与 _rebuild_index（详解专节）

```python
"retrieval_config": self.retrieval_config.to_dict(),
            "rerank_config": self.rerank_config.to_dict(),
            "rewrite_config": self.rewrite_config.to_dict(),
            "citation_config": self.citation_config.to_dict(),
            "expansion_config": self.expansion_config.to_dict(),
            "route_config": self.route_config.to_dict(),
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
```


**`_append_chunks`**：新块 `index` 从 `len(self.chunks)` 递增，避免与旧块冲突。每 append 同步追加 `KnowledgeDocument` 元数据行。

```python
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
```


**`_rebuild_index`（Day 25 核心）**：空库清空 embedding；非空则新建 `EmbeddingRetriever`，`export_state` 写入 `embedding_state`，教学版 TF-IDF 全量重训。Day 29 起可走 Chroma 增量，接口名保留。

## as_rag_service 缓存

```python
def as_rag_service(self) -> RAGContextService:
    if self._rag_service is None:
        self._rag_service = self._build_rag_service()
    return self._rag_service
```

`invalidate_cache()` 在每次索引变更后调用，防止返回过期 retriever。

详解附录完。

---

## 附录：ingest_text 错误路径（详解 vol2）

| 输入 | 异常 |
|------|------|
| content="" | ValueError 文档内容不能为空 |
| filename="" | ValueError filename 不能为空 |
| 正常 | 返回 KnowledgeDocument |

## load 边界

`load_json` 返回空时走 bootstrap，避免空对象导致空库无检索能力。

## 与 Day 19 chunker 参数

默认 chunk_size 200、overlap 40 来自 `ChunkConfig` 或显式参数。更改参数不改变 store version，但改变 chunk 边界，须文档告知运营「重建后检索变」。

详解 vol2 完。

---

## 实验课拓展

修改 chunk_size 为 50 观察 chunk_count 变化——为 Day 27 埋伏笔。

---

## 白板推导

陈默用三块磁贴：Document、Chunk、Embedding。学员上台排列 ingest_text 后磁贴增减顺序。白板推导完。
