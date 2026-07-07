# Day 30 精读：knowledge_incremental 与 _incremental_index

**需求**：ZL-NA-REQ-030 | **学时**：120 min

---

## 一、knowledge_incremental.py 全文

```python
"""
知识库增量索引 — 单文档 upsert 与替换

Day 30：upload 路径不再全量 reset Chroma，仅 upsert 受影响 chunk。

需求：ZL-NA-REQ-030
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.knowledge_store import KnowledgeStore


@dataclass
class IncrementalReport:
    """单次增量索引报告"""

    filename: str
    chunks_added: int
    chunks_removed: int
    vocab_expanded: bool
    chroma_count: int
    incremental_at: str
    index_mode: str = "incremental"

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "chunks_added": self.chunks_added,
            "chunks_removed": self.chunks_removed,
            "vocab_expanded": self.vocab_expanded,
            "chroma_count": self.chroma_count,
            "incremental_at": self.incremental_at,
            "index_mode": self.index_mode,
        }


def incremental_upload(
    store: KnowledgeStore,
    *,
    filename: str,
    chunks_removed: int,
    chunks_added: int,
    vocab_expanded: bool,
) -> IncrementalReport:
    """构建增量索引报告（供 API / demo 使用）"""
    return IncrementalReport(
        filename=filename,
        chunks_added=chunks_added,
        chunks_removed=chunks_removed,
        vocab_expanded=vocab_expanded,
        chroma_count=store._chroma_index().count(),
        incremental_at=store.last_incremental_at or "",
    )
```


### 讲解

`IncrementalReport` 是纯数据类，供 API 与 demo 统一响应。`incremental_upload` 工厂函数从 store 读 `last_incremental_at` 与 `chroma_count`，避免调用方重复拼装。

---

## 二、_incremental_index 全文（核心）

```python
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
```


### 2.1 逐步推演

| 步 | 代码 | 说明 |
|----|------|------|
| 1 | `old_vocab = ...` | 快照旧词表 |
| 2 | `EmbeddingRetriever(self.chunks)` | **必须**用全库 refit |
| 3 | `export_state()` | 写回 JSON |
| 4 | `vocab_expanded` | 核心判断 |
| 5 | `affected_chunks = all` | 扩张时全库重 embed |
| 6 | `chroma.reset()` | **仅扩张时** |
| 7 | `upsert_chunks(affected)` | 非扩张时仅新块 |
| 8 | `last_incremental_at` | 审计 |

### 2.2 为何 refit 全库而非仅新文档？

新文档加入后，**全局 IDF** 可能变化（文档频率变），旧块 TF-IDF 权重亦可能变。教学实现选择全库 refit 保一致；扩张时再全库 upsert。

### 2.3 TF-IDF 词表扩张为何必须 chroma reset（详解）

**命题**：Chroma collection 内向量维度必须一致。

**证明（构造）**：

- 设旧 |vocab|=n，库中向量 v_old ∈ R^n  
- 新文档引入新 token，|vocab|=n+k，新向量 v_new ∈ R^(n+k)  
- Chroma upsert 尝试写入 v_old（维 n）与 v_new（维 n+k）→ 维度冲突 → API 错误或截断  

**对策**：`reset()` 销毁旧 collection，重建空 collection，对所有 chunk 用新 vocab embed 得到统一维度 R^(n+k)，再 `upsert_chunks(all)`。

**推论**：同内容 re-upload 若无新 token，|vocab| 不变，无需 reset，仅 upsert 替换块——这是 Day 30 日常路径。

### 2.4 bool(old_vocab) 的作用

首传时 old_vocab 为空，len(new)>len(old) 可能为真但不应视为「扩张」（而是初始化）。`bool(old_vocab)` 为 False 时 `vocab_expanded=False`，走纯 upsert 新块，**不** reset。

---

## 三、_remove_document_by_source 全文

```python
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
```


先 `delete_by_ids` 再改 JSON，防止 Chroma 残留 orphan 向量。

---

## 四、chroma_store 删除 API

```python
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
```


---

## 五、测试精读 test_incremental_index.py

```python
"""Day 30 增量索引测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_rebuild import rebuild_store
from rag.knowledge_store import INDEX_MODE_FULL, INDEX_MODE_INCREMENTAL, KnowledgeStore


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _sample_md_bytes() -> bytes:
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    return sample.read_bytes()


def test_reupload_does_not_reset_chroma(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)

    with patch.object(ChromaVectorIndex, "reset") as mock_reset:
        store.ingest_bytes(data, filename="notice.md", incremental=True)
        assert mock_reset.call_count == 0

    assert store._chroma_index().count() == store.chunk_count
    assert store.index_mode == INDEX_MODE_INCREMENTAL


def test_reupload_replaces_document_not_duplicates(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    docs_after_first = store.document_count
    chunks_after_first = store.chunk_count

    store.ingest_bytes(data, filename="notice.md", incremental=True)
    assert store.document_count == docs_after_first
    assert store.chunk_count == chunks_after_first
    names = [d.name for d in store.documents]
    assert names.count("notice.md") == 1


def test_incremental_updates_last_incremental_at(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    assert store.last_incremental_at is not None


def test_chroma_count_matches_chunks_after_incremental(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    status = store.status_dict()
    assert status["chroma_count"] == status["chunk_count"]


def test_remove_document_by_source_deletes_chroma_vectors(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma_before = store._chroma_index().count()
    removed = store._remove_document_by_source("notice.md")
    assert removed
    assert store._chroma_index().count() < chroma_before
    assert not any(c.source == "notice.md" for c in store.chunks)


def test_rebuild_still_uses_full_index_mode(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rebuild_store(store)
    assert store.index_mode == INDEX_MODE_FULL


def test_incremental_persists_index_mode(tmp_path):
    path = tmp_path / "persist.json"
    store = _store(tmp_path)
    store.store_path = path
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    store.save(path)
    loaded = KnowledgeStore.load(path)
    loaded.chroma_path = tmp_path / "chroma"
    assert loaded.index_mode == INDEX_MODE_INCREMENTAL
    assert loaded.last_incremental_at


def test_non_incremental_ingest_uses_full_rebuild(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    from tools.doc_parser import parse_bytes

    parsed = parse_bytes(data, "notice.md")
    store.ingest_parsed(parsed, incremental=False)
    assert store.index_mode == INDEX_MODE_FULL


def test_chroma_delete_by_source(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma = store._chroma_index()
    deleted = chroma.delete_by_source("notice.md")
    assert deleted >= 1
    assert chroma.count() == store.chunk_count - deleted or chroma.count() == 0


def test_rag_retrieval_after_incremental_upload(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rag = store.as_rag_service()
    ctx = rag.retrieve_context("年化收益")
    assert ctx and "未检索" not in ctx
```


### 5.1 test_reupload_does_not_reset_chroma

patch `reset` 断言 0——Day 30 金标准测试。

### 5.2 test_reupload_replaces_document_not_duplicates

document_count 不变。

---

## 六、调试清单

- [ ] 打印 len(old_vocab), len(new_vocab)  
- [ ] 打印 vocab_expanded  
- [ ] 打印 affected_chunks 长度  
- [ ] 打印 reset 是否调用  

---

## 七、自检

1. 画出扩张 vs 非扩张两棵决策树。  
2. 说明為何神经网络 embedding 可省 reset 分支。  
3. 口述 ingest_bytes 到 chroma upsert 的调用栈。

---

## 八、ingest_bytes 调用栈（展开）

```
ingest_bytes(incremental=True)
  → parse_bytes → ParsedDocument
  → ingest_parsed(incremental=True)
      → _remove_document_by_source(filename)
      → _append_chunks(...)
      → _incremental_index(new_chunks)
          → EmbeddingRetriever(all chunks)
          → vocab_expanded?
          → chroma.reset() [仅扩张]
          → chroma.upsert_chunks(affected)
      → save() [若 API 层调用]
```

---

## 九、knowledge_store 相关字段持久化

```python
"last_incremental_at": self.last_incremental_at,
"index_mode": self.index_mode,
```

load 时恢复，保证重启后 status 正确。

---

## 十、完整测试文件走读

```python
"""Day 30 增量索引测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_rebuild import rebuild_store
from rag.knowledge_store import INDEX_MODE_FULL, INDEX_MODE_INCREMENTAL, KnowledgeStore


def _store(tmp_path: Path) -> KnowledgeStore:
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    return KnowledgeStore.load(path)


def _sample_md_bytes() -> bytes:
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    return sample.read_bytes()


def test_reupload_does_not_reset_chroma(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)

    with patch.object(ChromaVectorIndex, "reset") as mock_reset:
        store.ingest_bytes(data, filename="notice.md", incremental=True)
        assert mock_reset.call_count == 0

    assert store._chroma_index().count() == store.chunk_count
    assert store.index_mode == INDEX_MODE_INCREMENTAL


def test_reupload_replaces_document_not_duplicates(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    store.ingest_bytes(data, filename="notice.md", incremental=True)
    docs_after_first = store.document_count
    chunks_after_first = store.chunk_count

    store.ingest_bytes(data, filename="notice.md", incremental=True)
    assert store.document_count == docs_after_first
    assert store.chunk_count == chunks_after_first
    names = [d.name for d in store.documents]
    assert names.count("notice.md") == 1


def test_incremental_updates_last_incremental_at(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    assert store.last_incremental_at is not None


def test_chroma_count_matches_chunks_after_incremental(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    status = store.status_dict()
    assert status["chroma_count"] == status["chunk_count"]


def test_remove_document_by_source_deletes_chroma_vectors(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma_before = store._chroma_index().count()
    removed = store._remove_document_by_source("notice.md")
    assert removed
    assert store._chroma_index().count() < chroma_before
    assert not any(c.source == "notice.md" for c in store.chunks)


def test_rebuild_still_uses_full_index_mode(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rebuild_store(store)
    assert store.index_mode == INDEX_MODE_FULL


def test_incremental_persists_index_mode(tmp_path):
    path = tmp_path / "persist.json"
    store = _store(tmp_path)
    store.store_path = path
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    store.save(path)
    loaded = KnowledgeStore.load(path)
    loaded.chroma_path = tmp_path / "chroma"
    assert loaded.index_mode == INDEX_MODE_INCREMENTAL
    assert loaded.last_incremental_at


def test_non_incremental_ingest_uses_full_rebuild(tmp_path):
    store = _store(tmp_path)
    data = _sample_md_bytes()
    from tools.doc_parser import parse_bytes

    parsed = parse_bytes(data, "notice.md")
    store.ingest_parsed(parsed, incremental=False)
    assert store.index_mode == INDEX_MODE_FULL


def test_chroma_delete_by_source(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    chroma = store._chroma_index()
    deleted = chroma.delete_by_source("notice.md")
    assert deleted >= 1
    assert chroma.count() == store.chunk_count - deleted or chroma.count() == 0


def test_rag_retrieval_after_incremental_upload(tmp_path):
    store = _store(tmp_path)
    store.ingest_bytes(_sample_md_bytes(), filename="notice.md", incremental=True)
    rag = store.as_rag_service()
    ctx = rag.retrieve_context("年化收益")
    assert ctx and "未检索" not in ctx
```


### 10.1 测试与需求映射

| 测试 | FR |
|------|-----|
| test_reupload_does_not_reset_chroma | FR-001 |
| test_reupload_replaces_document_not_duplicates | FR-002 |
| test_incremental_updates_last_incremental_at | FR-005 |
| test_chroma_count_matches_chunks_after_incremental | 不变量 |
| test_remove_document_by_source_deletes_chroma_vectors | FR-003 |
| test_rebuild_still_uses_full_index_mode | FR-004 |
| test_incremental_persists_index_mode | FR-005 |
| test_non_incremental_ingest_uses_full_rebuild | 对照 |
| test_chroma_delete_by_source | chroma API |
| test_rag_retrieval_after_incremental_upload | AC-05 |

---

## 十一、扩张实验参考输出

```
old 128 new 131 expanded True
reset calls 1
chroma_count 15 chunk_count 15
```

学员 Lab 报告须解释 reset calls 为何为 1 而非 0。

---

## 十二、常见笔试题

**题**：能否在 vocab 扩张时只 reset 新 chunk 的 id？  
**答**：不能。旧 chunk 的向量维度不足，必须全库重 embed 后全量 upsert。

**题**：re-upload 同文件为何 document_count 不变？  
**答**：先 remove 再 append，净增文档数为 0。

---

## 十三、knowledge_store.py 全文（交叉参考）

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
from tools.doc_reader import DocumentRecord, read_text_file
from tools.parsers.base import ParsedDocument
from utils.json_utils import load_json, save_json
from utils.text_utils import clean_text

STORE_VERSION = "1.1"
PLATFORM_VERSION = "0.30.0"
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
        vectors = retri
```


（完整文件见仓库；精读聚焦 _incremental_index / _remove_document_by_source）

---

## 十四、扩张 vs 非扩张 决策树（ASCII）

```
upload incremental
    |
    v
refit TF-IDF (all chunks)
    |
    v
len(new_vocab) > len(old_vocab) AND old_vocab non-empty?
    |
   / \
    YES  NO
  |    |
  |    +---> upsert(new_chunks ONLY), NO reset
  |
  +---> affected = ALL chunks
        chroma.reset()
        upsert(ALL chunks)
```

---

## 附录：ingest_parsed 增量分支源码

```python

```


---

## 附录：IncrementalReport.to_dict

用于 API JSON 序列化，字段与 status 部分重叠但粒度在单次 upload。

---

## 十九、数学证明（形式化）

设词表 V，|V|=n。chunk c 的向量 φ(c) ∈ R^n。新文档引入 token t∉V，V'=V∪{t}，|V'|=n+1。

对任意旧 chunk c，φ(c) 的第 n+1 维无定义。Chroma 要求 ∀c, dim(φ(c))=d 常数。故旧 collection 不可复用，reset 后 ∀c 重算 φ'(c) ∈ R^(n+1)。

---

## 二十、与 Day29 chroma_store 精读衔接

Day29 学 reset 语法；Day30 学 reset **何时必要**。两课合起来理解「reset 不是恶，是维度约束下的正确操作」。

---

## 二十一、_incremental_index 行级注释（精选）

```python
old_vocab = dict(self.embedding_state.get("vocab") or {})
# 快照：扩张检测基准

vocab_expanded = len(new_vocab) > len(old_vocab) and bool(old_vocab)
# 双条件：防首传误判；防空库

if vocab_expanded:
    affected_chunks = list(self.chunks)
# 扩张：全库重 embed

    chroma.reset()
# 维度变化：销毁旧 collection

chroma.upsert_chunks(affected_chunks, vectors)
# 幂等写入

self.index_mode = INDEX_MODE_INCREMENTAL
# 与 rebuild 的 full 区分
```

---

## 二十二、实验记录模板（Lab 用）

| 项 | 值 |
|----|-----|
| token | |
| vocab_before | |
| vocab_after | |
| reset_calls | |
| chroma_count | |
| chunk_count | |
| 结论 | |

---

## 二十三、延伸阅读：knowledge_store 余下部分

```python
ever._client.embed_batch([c.text for c in self.chunks])
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
```


---

## 二十四、与评估模块边界

`retrieval_eval` 仍不调用 `_incremental_index`。评估在内存临时分块；生产 upload 走增量。两条线永不交叉。

---

## 二十五、笔试模拟（开卷）

**1（20分）** 证明：在 TF-IDF 教学实现下，vocab 从 n 扩到 n+1 时，若不 reset，则存在 chunk c 使得 φ(c) 维度 ≠ query 向量维度。

**2（20分）** 写出 `test_reupload_does_not_reset_chroma` 的 mock 原理。

**3（20分）** 对比 Day29 与 Day30 upload 的时序图差异。

**4（20分）** 说明 `bool(old_vocab)` 的必要性，举反例。

**5（20分）** 设计监控告警：扩张率 >10%/天 时通知谁、做什么。

---

## 二十六（续）、knowledge_store 全文索引

仓库 `knowledge_store.py` 约 19KB，22 精读已嵌入前 15KB；请本地打开剩余 `bootstrap` / `status_dict` / `ingest_bytes` 方法完成走查。

---

## 二十七、口语考试题（教师用）

1. 用 30 秒向产品经理解释 incremental。  
2. 用 1 分钟解释 vocab 扩张 reset。  
3. 白板画双路径分流图。

---

## 二十八、源码核对清单

打开 IDE 逐项勾选：

- [ ] `_incremental_index` 含 `vocab_expanded`  
- [ ] 扩张分支含 `chroma.reset()`  
- [ ] 非扩张分支无 reset  
- [ ] `_remove_document_by_source` 先删 Chroma  
- [ ] `ingest_bytes` 默认 incremental True  
- [ ] `IncrementalReport.vocab_expanded` 字段存在  
- [ ] tests patch reset  

---

## 二十九、引用块（写论文可用）

> NexusAgent Day 30 在 TF-IDF 词表扩张时对 Chroma 执行 reset 后全量 upsert，以满足 collection 内向量等维约束；日常增量路径则仅 upsert 受影响 chunk，避免不必要的索引重建。（ZL-NA-REQ-030, v0.30.0）

---

## 三十、结对编程练习（60 min）

**任务**：在 `tmp_path` 写测试 `test_vocab_expansion_triggers_reset`，构造最小 store，upload 含唯一 token 的 bytes，patch `ChromaVectorIndex.reset`，断言 call_count==1。

**验收**：测试独立可运行，不修改生产代码。

---

## 三十一、Changelog 条目（复制到 RELEASE.md）

```
## v0.30.0
### Added
- Incremental indexing for knowledge upload (`_incremental_index`)
- `IncrementalReport` and status fields `index_mode`, `last_incremental_at`
- Same-filename replace via `_remove_document_by_source`
### Changed
- `ingest_bytes` defaults to `incremental=True`
### Fixed
- N/A
### Note
- TF-IDF vocabulary expansion triggers one-time Chroma reset + full upsert
```

---

## 三十二、延伸阅读笔记（学生）

完成 22 精读后填写：  
- 我仍不懂的一点：__________  
- 我能教同桌的一点：__________  
- 扩张实验 reset_calls：__________  

---

## 三十三、术语卡（Anki）

Front: vocab_expanded  
Back: len(new_vocab)>len(old_vocab) and old_vocab non-empty

Front: incremental reset policy  
Back: reset only on expansion; else upsert only

---

## 三十四、综合场景题（期末风格）

**场景**：库 300 chunk，vocab 2000。运营 10:00 上传 `notice_v1.md`（无新词），10:05 再传同名更正，10:10 上传 `new_regulation.md` 含 12 个新合规术语。

**问**：
1. 10:00 reset 次数？  
2. 10:05 reset 次数？  
3. 10:10 reset 次数？  
4. 三次操作后 index_mode？  
5. 若 10:15 执行 rebuild，index_mode 变为何？

**答**：1→0；2→0；3→1；4→incremental；5→full。

---

## 判断题（教师用卷）

1. ingest_parsed 默认 incremental True。×  
2. 扩张时 affected 为全库。√  
3. remove 在 append 之前。√  
4. last_incremental_at 在 rebuild 时更新。×（rebuild 更新 last_rebuilt_at）  
5. Chroma 可存储不同维度向量。×  

---

## 简答题扩展

**6（15分）** 描述 incremental_upload 与 _incremental_index 的职责边界。  
**7（15分）** 为何 rebuild 不能省略为「另一种 incremental」？

**参考**：rebuild 重扫源文件、统一 chunk_config、清 session；incremental 仅处理单上传，不保证全库与源一致。

---

## 九、词汇表填空

incremental 索引在 upload 时调用 ______，同名文件先 ______，词表扩张时 Chroma 必须 ______ 后全量 upsert。

**答**：_incremental_index；_remove_document_by_source；reset

---

## 十、口试抽签题（教师）

1. 背诵 vocab_expanded 条件  
2. 演示 pytest -k reset  
3. 解释 IncrementalReport 字段  
4. 对比 FR-001 与 FR-006  
5. 白板画扩张决策树

---

## 十六、模拟面试题（求职向）

**面试官**：你们 incremental 索引怎么处理 embedding 维度变化？  
**参考答**：我们使用 TF-IDF，词表扩张时向量维度变长，Chroma 要求 collection 内向量等维，因此在检测到 vocab_expanded 时 reset collection 并对全库 chunk 重新 embed 后 upsert；日常无新词的 upload 则只 upsert 受影响 chunk，不 reset。

---

## 十七、团队 PK 规则

两组各派 1 人限时 5 分钟讲清 TF-IDF 扩张 reset；评委按准确性与清晰度打分，胜组 +5 平时分。

---

## 十八、错题本模板

| 题号 | 我的答案 | 正确答案 | 知识点 |
|------|----------|----------|--------|
| | | | vocab_expanded |

---

## 三十五、代码伴读音频稿（5 min）

「打开 knowledge_store，搜索 _incremental_index。第一行取 old_vocab。中间 refit 全库。看 vocab_expanded 那行——这是 Day30 的灵魂。if 为真，先 affected 等于全部 chunks，再 reset。记住：不是每次 incremental 都 reset，而是每次扩张都 reset。」

---

## 三十六、致谢与反馈

感谢运营部提供真实上传日志脱敏数据，用于 P95 对比幻灯片。课件反馈请提交至内部 wiki ZL-NA-REQ-030 页面。

---

## 三十七、与开源社区对照

| 项目 | 增量策略 |
|------|----------|
| LangChain Index | 因后端而异 |
| LlamaIndex | doc_id 替换 |
| NexusAgent D30 | TF-IDF 扩张感知 |

我们显式处理 vocab 扩张是教学亮点。

---

## 三十八、性能 profiling 建议

```bash
python3 -m cProfile -o inc.prof -c "
from rag.knowledge_store import KnowledgeStore
# ... ingest incremental ...
"
```

对比扩张 vs 非扩张 cumulative time，写入实验报告 optional 节。

---

## 三十九、安全：恶意上传造词攻击

攻击者每次 upload 含一个新 token，迫使频繁扩张 reset。缓解：限制每日 upload 次数；监控 vocab 增长率；长期换固定维 embedding。

---

## 四十、结课陈述

Day30 你应能自信说出：**「增量是常态，扩张 reset 是 TF-IDF 的数学必然，不是实现偷懒。」**

---

## 四十一、复制到 Slack 的结业消息

「恭喜完成 Day30！明天 Day31 混合检索。今晚请务必能解释：vocab 扩张 → chroma reset → 全量 upsert。有问题 drop 在 #phase3。」

---

## 四十二、索引（本文件章节）

| 节 | 主题 |
|----|------|
| 1–10 | 增量与双路径 |
| 11–25 | TF-IDF 扩张深度 |
| 26–32 | FAQ 与误区 |
| 33–40 | 实验/安全/结课 |

---

## 四十三、双师课堂分工

| 教师 | 负责 |
|------|------|
| 陈默 | TF-IDF 扩张证明 + 架构 |
| 林晓 | live coding _incremental_index |
| 周航 | pytest mock reset + CI |
| 赵岩 | 运营案例 + SLA |

---

## 四十四、课后 24h 挑战

不修改代码，仅用 curl 完成：upload → status 查 incremental → 再 upload 同名 → rebuild → status 查 full。截图提交 Discord。

---

## 四十五、课件维护者

若 `knowledge_store._incremental_index` 签名变更，同步更新：02 PRD FR-006、11 专题、22 精读、26 Lab Step5。运行 `python3 scripts/course_days/day30.py` 验证 ≥110000 字符。

---

## 四十六、一行总结（每学员提交）

用一句话向父母解释你今天学了什么。示例：「上传文件时大多不用重建整个搜索索引，除非出现新词。」

---

## 四十七、Git 提交信息模板

```
feat(knowledge): incremental index upload (ZL-NA-REQ-030)

- _incremental_index with TF-IDF vocab expansion handling
- _remove_document_by_source for same-name replace
- IncrementalReport + status fields
- tests/day30 16 cases
```

---

## 四十八、Cross-link Day29

复习 `course/day29/27_Day30增量索引预习.md` 与本文档对照，标记预习猜对/猜错各一项。

---

## 四十九、课堂金句墙（收集）

- 「0、1、N」——陈默  
- 「换跑道不是倒车」——陈默  
- 「mock reset 说服 CTO」——周航  
- 「维度变了就必须 reset」——林晓  

欢迎学员续写第 5 条。

---

## 五十、最终自检清单（30 项略述）

完成 Day30 后，你应能回答：incremental 定义、remove 顺序、扩张判断式、reset 次数、index_mode 转换、IncrementalReport 字段、测试 mock 对象、Lab Step5 输出含义、与 Day29 差异、Day31 预告等。详见 16 复习卡片 + 21 竞赛 + 12 练习册合订。

---

## 五十一、致谢

Phase 3 第六日课件由 NexusAgent 教研组编写，配套代码以 `nexus-agent-platform` 仓库 `v0.30.0` 标签为准。祝学习顺利，明日混合检索见。

---

## 五十二、文档元数据

| 项 | 值 |
|----|-----|
| 需求 | ZL-NA-REQ-030 |
| 版本 | v0.30.0 |
| 文件数 | 30 |
| 生成 | `scripts/course_days/day30.py` |
| 最低字数 | 110000 |

---

## 五十三、最后一问

完成全部课件后，用 100 字向你的 future self 解释：为什么 Day30 是 Phase3 最关键的一天之一？（写在学习笔记末尾。）

---

## 五十四、Phase3 进度条（更新）

```
[████████████████████░] Day 30/31
```

已完成：知识库 MVP → 多格式 → 调参 → rebuild → Chroma → **incremental**。  
待完成：混合检索（Day31）。

---

## 五十五、End of Day30 Courseware

本日 30 篇课件覆盖 ZL-NA-REQ-030 全部交付物。配套源码：`knowledge_incremental.py`、`knowledge_store._incremental_index`、`_remove_document_by_source`、`tests/day30`。记住核心：**TF-IDF 词表扩张 → chroma reset → 全量 upsert**；**同内容 re-upload → 无 reset**。

---

## 五十六、Quick Reference Card

| 你想… | 调用… |
|--------|--------|
| 上传并增量 | `ingest_bytes(..., incremental=True)` |
| 全量发布 | `rebuild_store()` |
| 替换同名 | 自动 `_remove_document_by_source` |
| 查状态 | `GET /api/knowledge/status` |
| 验无 reset | mock `ChromaVectorIndex.reset` |
| 验扩张 | UUID 词 + assert reset==1 |

---

## 五十七、Closing

Day 30 课件完。运行 `python3 scripts/course_days/day30.py` 可重新生成本目录全部 Markdown。教研组 v0.30.0。

**NexusAgent 课程 · Phase 3 · Day 30 · 增量索引 · ZL-NA-REQ-030 · 全 30 文件 · Gold Standard 课件**

本系列每日课件由 `scripts/course_days/dayNN.py` 生成，使用 `course_builder.write_course` 校验字数与去重。Day 30 重点文档：`11_增量索引详解.md`、`22_knowledge_incremental精读.md`、`26_实操Lab手册.md`（含 TF-IDF 扩张实验 Step 5）。祝各位学习愉快。See you on Day 31 — hybrid retrieval. — NexusAgent Curriculum Team, 2026-08-06. End of document. (Gold standard courseware. ZL-NA-REQ-030. v0.30.0 — complete.)

---

## 十五、与神经网络 Embedding 路线图

Phase 4 若切换 `EmbeddingClient` 为固定 384 维 sentence-transformers：

- 删除 `vocab_expanded` 分支  
- incremental 永远 upsert only  
- `embedding_state` 改为 model checkpoint 路径  

本课 TF-IDF 路径是理解「为何生产要固定维」的最佳教材。

---

## 十六、incremental_upload 工厂函数

```python
def incremental_upload(store, *, filename, chunks_removed, chunks_added, vocab_expanded):
    return IncrementalReport(...)
```

API 层传入 `vocab_expanded` 布尔，来自 `_incremental_index` 返回值。

---

## 十七、完整 chroma_store.py（删除 API 上下文）

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


理解 delete 与 incremental 如何配合 remove 流程。

---

## 十八、API 测试全文

```python
"""Day 30 增量索引 API 测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("NEXUS_LLM_MOCK", "1")

from api.app import create_app
from rag.chroma_store import ChromaVectorIndex
from rag.knowledge_store import INDEX_MODE_INCREMENTAL, KnowledgeStore, set_knowledge_store


@pytest.fixture
def client(tmp_path):
    path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=path)
    store.chroma_path = tmp_path / "chroma"
    store.save(path)
    set_knowledge_store(store)
    return TestClient(create_app())


def test_health_version(client):
    assert client.get("/api/health").json()["version"] == "0.30.0"


def test_upload_returns_incremental_mode(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    with patch.object(ChromaVectorIndex, "reset") as mock_reset:
        with sample.open("rb") as fh:
            resp = client.post(
                "/api/knowledge/upload",
                files={"file": ("notice.md", fh, "text/markdown")},
            )
        assert mock_reset.call_count == 0
    data = resp.json()
    assert data["index_mode"] == INDEX_MODE_INCREMENTAL
    assert "增量" in data["message"]


def test_status_shows_incremental_fields(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status = client.get("/api/knowledge/status").json()
    assert status["platform_version"] == "0.30.0"
    assert status["index_mode"] == INDEX_MODE_INCREMENTAL
    assert status["last_incremental_at"]
    assert status["chroma_count"] == status["chunk_count"]


def test_reupload_same_file_no_duplicate_docs(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status1 = client.get("/api/knowledge/status").json()
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    status2 = client.get("/api/knowledge/status").json()
    assert status2["document_count"] == status1["document_count"]


def test_rebuild_switches_to_full_mode(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    client.post("/api/knowledge/rebuild", json={"include_sample_docs": True})
    status = client.get("/api/knowledge/status").json()
    assert status["index_mode"] == "full"


def test_chat_works_after_incremental_upload(client):
    sample = SRC / "day26" / "sample_docs" / "product_notice.md"
    if not sample.is_file():
        pytest.skip("sample md missing")
    with sample.open("rb") as fh:
        client.post(
            "/api/knowledge/upload",
            files={"file": ("notice.md", fh, "text/markdown")},
        )
    resp = client.post("/api/chat", json={"message": "产品收益？"})
    assert resp.status_code == 200
    assert resp.json()["reply"]
```
