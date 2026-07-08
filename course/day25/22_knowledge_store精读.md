# knowledge_store.py 精读

**需求**：ZL-NA-REQ-025 | **文件**：`nexus-agent-platform/src/rag/knowledge_store.py`

---

## 模块 docstring 与导入

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
```


**解读**：模块定位「可写入、可落盘的企业知识库 MVP」。导入链显示依赖 Day 19 `chunker`、Day 20 embedding、路径 `core.paths`。

---

## KnowledgeDocument 元数据类

```python
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
```


**解读**：
- `name` 即 source 文件名，与 chunks 的 `source` 字段对应  
- `ingested_at` ISO UTC 时间戳，审计用  
- `format` 默认 txt，Day 26 扩展 markdown/pdf  
- `to_dict`/`from_dict` 保证 JSON 往返  

---

## KnowledgeStore 字段

```python
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
```


**解读**：
- `documents` 与 `chunks` 分离：前者统计，后者检索  
- `_rag_service` 缓存避免重复构建 EmbeddingRetriever  
- `chunk_config` 为 Day 27 预留，Day 25 用默认  

---

## ingest_text 核心写入

```python
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
```


**逐行要点**：
1. L126-130：空内容与空文件名防御性校验  
2. L133-134：`clean_text` 去噪，FAQ 场景建议开启  
3. L135-141：构造 `DocumentRecord` 保留原始与 cleaned  
4. L142-147：`chunk_documents` 复用 Day 19 算法  
5. L148-149：`_append_chunks` + `_rebuild_index` 原子更新内存索引  

---

## save 持久化 envelope

```python
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
```


**解读**：`STORE_VERSION` 是 schema 版本；`platform_version` 标记平台里程碑；`chunks` 全量序列化教学透明但体积大。

---

## load / load_or_bootstrap

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
```


**解读**：`load_or_bootstrap` 是 API 冷启动唯一入口；不存在文件时 bootstrap 并立即 save，避免每次请求重复引导。

---

## bootstrap_from_sample_docs

```python
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
```


**解读**：从既有 `RAGContextService.from_sample_docs` 迁移数据，保证 Day 24 行为回归；按 source 分组生成 `KnowledgeDocument` 列表。

---

## 单例 get_knowledge_store

```python
_store: KnowledgeStore | None = None
_store_lock = threading.Lock()


def get_knowledge_store(*, reload: bool = False) -> KnowledgeStore:
    """全局知识库单例（API 与 factory 共享）"""
    global _store
    with _store_lock:
        if _store is None or reload:
            _store = KnowledgeStore.load_or_bootstrap()
        return _store
```


**解读**：`threading.Lock` + 全局 `_store`；`reload=True` 强制重载（运维场景）；测试用 `set_knowledge_store` 注入假实例。

---

## 与测试对照

| 测试 | 覆盖代码 |
|------|----------|
| test_save_and_load_roundtrip | save/load + retrieve |
| test_ingest_text_appends_chunks | ingest_text |
| test_bootstrap_has_chunks | bootstrap |

精读完。结合 [25_ingestion流水线精读.md](25_ingestion流水线精读.md)。

---

## 扩展精读：ingest_file 与 ingest_bytes

```python
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
```


**ingest_file**：面向运维脚本，`read_text_file` 读磁盘编码；参数 `chunk_size=200` 显式默认。  
**ingest_bytes**：API 热路径；Day 26 起内部 `from tools.doc_parser import parse_bytes`，Day 25 学员理解「二进制统一入口」即可。

---

## 扩展精读：as_rag_service 与 _build_rag_service

```python
"""构建或返回缓存的 RAGContextService"""
        if self._rag_service is None:
            self._rag_service = self._build_rag_service()
        return self._rag_service

    def invalidate_cache(self) -> None:
        self._rag_service = None

    def get_chunk_config(self) -> ChunkConfig:
        return ChunkConfig.from_dict(self.chunk_config.to_dict())
```


缓存 `_rag_service` 避免每次 chat 重建 EmbeddingRetriever。`invalidate_cache` 在 `_rebuild_index` 末尾调用，保证下次 `as_rag_service` 重建。

---

## 扩展精读：完整测试文件 test_knowledge_store.py

```python
"""Day 25 知识库存储与 ingestion 测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.paths import get_path
from day25.constants import SAMPLE_UPLOAD_TEXT
from rag.embedding import TfidfEmbeddingModel
from rag.ingestion import ingest_upload
from rag.knowledge_store import KnowledgeStore, get_knowledge_store, set_knowledge_store


@pytest.fixture
def tmp_store(tmp_path):
    store_path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=store_path)
    set_knowledge_store(store)
    yield store
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())


def test_bootstrap_has_chunks(tmp_store):
    assert tmp_store.document_count >= 1
    assert tmp_store.chunk_count >= 3


def test_ingest_text_appends_chunks(tmp_store):
    before = tmp_store.chunk_count
    meta = tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="extra.txt")
    assert meta.chunk_count > 0
    assert tmp_store.chunk_count == before + meta.chunk_count


def test_rag_retrieve_after_ingest(tmp_store):
    tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="faq_extra.txt")
    ctx = tmp_store.as_rag_service().retrieve_context("最低起购金额")
    assert "1000" in ctx or "起购" in ctx


def test_save_and_load_roundtrip(tmp_store, tmp_path):
    path = tmp_path / "roundtrip.json"
    tmp_store.ingest_text("测试持久化文本内容。", filename="persist.txt")
    tmp_store.save(path)

    loaded = KnowledgeStore.load(path)
    assert loaded.chunk_count == tmp_store.chunk_count
    assert loaded.document_count == tmp_store.document_count
    ctx = loaded.as_rag_service().retrieve_context("持久化")
    assert "持久化" in ctx


def test_embedding_export_load_state():
    model = TfidfEmbeddingModel()
    model.fit(["年化收益", "风险提示", "起购金额"])
    state = model.export_state()
    restored = TfidfEmbeddingModel()
    restored.load_state(state)
    assert restored.is_fitted
    assert restored.dimension == model.dimension


def test_status_dict(tmp_store):
    data = tmp_store.status_dict()
    assert data["chunk_count"] == tmp_store.chunk_count
    assert data["platform_version"] == "0.30.0"
    assert isinstance(data["documents"], list)


def test_get_knowledge_store_singleton(tmp_store):
    a = get_knowledge_store()
    b = get_knowledge_store()
    assert a is b


def test_ingest_upload_writes_file(tmp_store, tmp_path, monkeypatch):
    monkeypatch.setitem(
        __import__("core.paths", fromlist=["PATHS"]).PATHS,
        "knowledge_uploads",
        tmp_path / "uploads",
    )
    data = SAMPLE_UPLOAD_TEXT.encode("utf-8")
    meta = ingest_upload(data, "uploaded.txt", store=tmp_store, uploads_dir=tmp_path / "uploads")
    assert meta.name == "uploaded.txt"
    assert (tmp_path / "uploads" / "uploaded.txt").is_file()


def test_ingest_empty_raises(tmp_store):
    with pytest.raises(ValueError):
        tmp_store.ingest_text("   ", filename="empty.txt")


def test_store_json_has_version(tmp_store, tmp_path):
    path = tmp_path / "v.json"
    tmp_store.save(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == "1.1"
    assert raw["platform_version"] == "0.30.0"
```


| 测试 | 教学要点 |
|------|----------|
| test_bootstrap_has_chunks | 引导后至少有 sample 块 |
| test_rag_retrieve_after_ingest | 证明写入即可检索 |
| test_save_and_load_roundtrip | 持久化是 Day 25 核心 |
| test_ingest_upload_writes_file | 审计副本在 uploads/ |
| test_store_json_has_version | schema 契约 |

---

## 扩展精读：ingest_parsed（Day 26 衔接）

```python
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


---

## 扩展精读：frontend knowledge.js

```javascript
/**
 * NexusAgent Day 25 — 知识库侧栏（上传与状态）
 *
 * 需求：ZL-NA-REQ-025
 */
(function (global) {
  "use strict";

  async function fetchStatus() {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/status`);
    if (!res.ok) {
      throw new Error(`status ${res.status}`);
    }
    return res.json();
  }

  async function uploadFile(file) {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const form = new FormData();
    form.append("file", file, file.name);
    const res = await fetch(`${base}/api/knowledge/upload`, {
      method: "POST",
      body: form,
    });
    const payload = await (global.NexusErrors
      ? NexusErrors.parseErrorResponse(res)
      : res.json().catch(() => ({})));
    if (!res.ok) {
      const msg = global.NexusErrors
        ? NexusErrors.mapApiError(res.status, payload)
        : `上传失败（${res.status}）`;
      throw new Error(msg);
    }
    return payload;
  }

  function renderStatus(el, data) {
    if (!el || !data) return;
    const docs = (data.documents || [])
      .map((d) => d.name)
      .slice(-5)
      .join("、");
    el.textContent = `${data.document_count} 篇 / ${data.chunk_count} 块${
      data.index_mode ? " · " + data.index_mode : ""
    }${docs ? " · " + docs : ""}`;
  }

  async function runEvaluate() {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ use_presets: true }),
    });
    if (!res.ok) {
      throw new Error(`evaluate ${res.status}`);
    }
    return res.json();
  }

  async function runRebuild(applyBest) {
    const base = (global.NexusConfig && global.NexusConfig.apiBase) || "";
    const res = await fetch(`${base}/api/knowledge/rebuild`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        include_sample_docs: true,
        apply_best_config: !!applyBest,
      }),
    });
    if (!res.ok) {
      throw new Error(`rebuild ${res.status}`);
    }
    return res.json();
  }

  function bindPanel() {
    const panel = document.getElementById("kb-panel");
    const toggle = document.getElementById("kb-toggle");
    const statusEl = document.getElementById("kb-status");
    const fileInput = document.getElementById("kb-file");
    const uploadBtn = document.getElementById("kb-upload-btn");
    const evalBtn = document.getElementById("kb-eval-btn");
    const rebuildBtn = document.getElementById("kb-rebuild-btn");
    const msgEl = document.getElementById("kb-message");

    if (!panel) return;

    if (global.NexusConfig && global.NexusConfig.useMock) {
      if (statusEl) statusEl.textContent = "Mock 模式不可用";
      return;
    }

    async function refresh() {
      try {
        const data = await fetchStatus();
        renderStatus(statusEl, data);
      } catch (_e) {
        if (statusEl) statusEl.textContent = "知识库离线";
      }
    }

    if (toggle) {
      toggle.addEventListener("click", () => {
        panel.classList.toggle("kb-panel--open");
      });
    }

    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener("click", async () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
          if (msgEl) msgEl.textContent = "请选择 .txt / .md / .pdf 文件";
          return;
        }
        if (msgEl) msgEl.textContent = "上传中…";
        try {
          const result = await uploadFile(file);
          if (msgEl) {
            msgEl.textContent = `${result.message}（+${result.chunk_count} 块）`;
          }
          fileInput.value = "";
          await refresh();
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "上传失败";
        }
      });
    }

    if (evalBtn) {
      evalBtn.addEventListener("click", async () => {
        if (msgEl) msgEl.textContent = "评估中…";
        try {
          const result = await runEvaluate();
          const best = result.best_config || {};
          if (msgEl) {
            msgEl.textContent = `推荐: ${best.name || "—"} size=${best.chunk_size} hit@1 实验完成`;
          }
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "评估失败";
        }
      });
    }

    if (rebuildBtn) {
      rebuildBtn.addEventListener("click", async () => {
        if (msgEl) msgEl.textContent = "重建中…";
        try {
          const result = await runRebuild(false);
          if (msgEl) {
            msgEl.textContent = `${result.message}（${result.chunks_before}→${result.chunks_after} 块）`;
          }
          await refresh();
        } catch (err) {
          if (msgEl) msgEl.textContent = err.message || "重建失败";
        }
      });
    }

    refresh();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindPanel);
  } else {
    bindPanel();
  }

  global.NexusKnowledge = {
    fetchStatus,
    uploadFile,
    runEvaluate,
    runRebuild,
    renderStatus,
  };
})(window);
```




---

## 附录：status_dict 与测试对照（精读专节）

```python
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
```


`status_dict` 是 API 与 store 的桥梁。Day 25 学员重点看 `document_count`/`chunk_count`/`documents`；`supported_formats` 为 Day 26 预埋。

## ingest_file 与 ingest_bytes 对比

- `ingest_file`：运维脚本读磁盘，Day 25 txt 直读  
- `ingest_bytes`：API 上传入口，Day 26 内部分派 parser  

## 测试源码对照

```python
ngest_upload
from rag.knowledge_store import KnowledgeStore, get_knowledge_store, set_knowledge_store


@pytest.fixture
def tmp_store(tmp_path):
    store_path = tmp_path / "store.json"
    store = KnowledgeStore.bootstrap_from_sample_docs(store_path=store_path)
    set_knowledge_store(store)
    yield store
    set_knowledge_store(KnowledgeStore.bootstrap_from_sample_docs())


def test_bootstrap_has_chunks(tmp_store):
    assert tmp_store.document_count >= 1
    assert tmp_store.chunk_count >= 3


def test_ingest_text_appends_chunks(tmp_store):
    before = tmp_store.chunk_count
    meta = tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="extra.txt")
    assert meta.chunk_count > 0
    assert tmp_store.chunk_count == before + meta.chunk_count


def test_rag_retrieve_after_ingest(tmp_store):
    tmp_store.ingest_text(SAMPLE_UPLOAD_TEXT, filename="faq_extra.txt")
    ctx = tmp_store.as_rag_service().retrieve_context("最低起购金额")
    assert "1000" in ctx or "起购" in ctx


def test_save_and_load_roundtrip(tmp_store, tmp_path):
    path = tmp_path / "roundtrip.json"
    tmp_store.ingest_text("测试持久化文本内容。", filename="persist.txt")
    tmp_store.save(path)

    loaded = KnowledgeStore.load(path)
    assert loaded.chunk_count == tmp_store.chunk_count
    assert loaded.document_count == tmp_store.document_count
    ctx = loaded.as_rag_service().retrieve_context("持久化")
    assert "持久化" in ctx


def test_embedding_export_load_state():
    model = TfidfEmbeddingModel()
    model.fit(["年化收益", "风险提示", "起购金额"])
    state = model.export_state()
    restored = TfidfEmbeddingModel()
    restored.load_state(state)
    assert restored.is_fitted
    assert restored.dimension == model.dimension


def test_status_dict(tmp_store):
    data = tmp_store.status_dict()
    assert data["chunk_count"] == tmp_store.chunk_count
    assert data["platform_version"] == "0.30.0"
    assert isinstance(data["documents"], list)


def test_get_knowledge_store_singleton(tmp_store):
    a = get_knowledge_store()
    b = get_knowledge_store()
    assert a is b


def test_ingest_upload_writes_file(tmp_store, tmp_path, monkeypatch):
    monkeypatch.setitem(
        __import__("core.paths", fromlist=["PATHS"]).PATHS,
        "knowledge_uploads",
        tmp_path / "uploads",
    )
    data = SAMPLE_UPLOAD_TEXT.encode("utf-8")
    meta = ingest_upload(data, "uploaded.txt", store=tmp_store, uploads_dir=tmp_path / "uploads")
    assert meta.name == "uploaded.txt"
    assert (tmp_path / "uploads" / "uploaded.txt").is_file()


def test_ingest_empty_raises(tmp_store):
    with pytest.raises(ValueError):
        tmp_store.ingest_text("   ", filename="empty.txt")


def test_store_json_has_version(tmp_store, tmp_path):
    path = tmp_path / "v.json"
    tmp_store.save(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == "1.1"
    assert raw["platform_version"] == "0.30.0"
```


精读附录完。

---

## 附录：源码行号索引（精读 vol2）

| 行区 | 符号 | 学员掌握度 |
|------|------|------------|
| 35-62 | KnowledgeDocument | 必会 |
| 112-150 | ingest_text | 必会 |
| 255-272 | save | 必会 |
| 297-305 | load_or_bootstrap | 必会 |
| 307-334 | bootstrap | 理解 |
| 508-519 | get_knowledge_store | 必会 |
| 433-449 | _rebuild_index | 理解 |

## 节选：_chunk_to_dict

```python
def _chunk_to_dict(chunk: TextChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "source": chunk.source,
        "index": chunk.index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
    }
```


JSON 序列化丢弃 runtime 对象，只留可恢复字段。

精读 vol2 完。

---

## 教师演示脚本

打开 knowledge_store.py，滚动到 ingest_text，逐行停顿 10 秒让学员记笔记。

强调 _rebuild_index 是 Day 25 性能瓶颈也是教学重点。

---

## 源码打印建议

推荐打印 L35–334 与 L508–519；三色笔标注副作用/持久化/单例。打印建议完。

## KnowledgeStore 与 Day 26 衔接专节

Day 25 `ingest_bytes` 在 Day 26 仓库中首行调用 `parse_bytes`：

```python
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
```


学员须理解：Day 25 课件聚焦 txt MVP；仓库已向前兼容多格式，实验以 tests/day26 为准。

## _rebuild_index 与 _incremental_index

全量 rebuild 用于 Day 25 教学简单路径；Day 26 upload 可走 incremental（见仓库 `ingest_parsed(incremental=True)` 默认上传路径）。

衔接专节完。
