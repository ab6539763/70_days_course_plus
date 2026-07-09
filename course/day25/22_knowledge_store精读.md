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
```


**解读**：模块定位「可写入、可落盘的企业知识库 MVP」。导入链显示依赖 Day 19 `chunker`、Day 20 embedding、路径 `core.paths`。

---

## KnowledgeDocument 元数据类

```python
from rag.retrieval_config import RetrievalConfig
from rag.rewrite_config import RewriteConfig
from rag.rewriting_retriever import RewritingRetriever
from tools.doc_reader import DocumentRecord, read_text_file
from tools.parsers.base import ParsedDocument
from utils.json_utils import load_json, save_json
from utils.text_utils import clean_text

STORE_VERSION = "1.1"
PLATFORM_VERSION = "0.39.0"
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
```


**解读**：
- `name` 即 source 文件名，与 chunks 的 `source` 字段对应  
- `ingested_at` ISO UTC 时间戳，审计用  
- `format` 默认 txt，Day 26 扩展 markdown/pdf  
- `to_dict`/`from_dict` 保证 JSON 往返  

---

## KnowledgeStore 字段

```python
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
```


**解读**：
- `documents` 与 `chunks` 分离：前者统计，后者检索  
- `_rag_service` 缓存避免重复构建 EmbeddingRetriever  
- `chunk_config` 为 Day 27 预留，Day 25 用默认  

---

## ingest_text 核心写入

```python
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
```


**解读**：`STORE_VERSION` 是 schema 版本；`platform_version` 标记平台里程碑；`chunks` 全量序列化教学透明但体积大。

---

## load / load_or_bootstrap

```python
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
```


**解读**：`load_or_bootstrap` 是 API 冷启动唯一入口；不存在文件时 bootstrap 并立即 save，避免每次请求重复引导。

---

## bootstrap_from_sample_docs

```python
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
```


**解读**：从既有 `RAGContextService.from_sample_docs` 迁移数据，保证 Day 24 行为回归；按 source 分组生成 `KnowledgeDocument` 列表。

---

## 单例 get_knowledge_store

```python
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
```


**ingest_file**：面向运维脚本，`read_text_file` 读磁盘编码；参数 `chunk_size=200` 显式默认。  
**ingest_bytes**：API 热路径；Day 26 起内部 `from tools.doc_parser import parse_bytes`，Day 25 学员理解「二进制统一入口」即可。

---

## 扩展精读：as_rag_service 与 _build_rag_service

```python
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
    assert data["platform_version"] == "0.39.0"
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
    assert raw["platform_version"] == "0.39.0"
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
      data.validation_config && data.validation_config.enabled
        ? " · validate"
        : data.route_config && data.route_config.enabled
        ? " · route"
        : data.expansion_config && data.expansion_config.enabled
        ? " · expand"
        : data.citation_config && data.citation_config.enabled
        ? " · cite"
        : data.rewrite_config && data.rewrite_config.enabled === false
          ? " · no-rewrite"
          : data.rewrite_config && data.rewrite_config.enabled
            ? " · rewrite"
            : data.rerank_config && data.rerank_config.enabled === false
              ? " · recall-only"
              : data.rerank_config && data.rerank_config.enabled
                ? " · rerank"
                : data.retrieval_config && data.retrieval_config.mode
                  ? " · " + data.retrieval_config.mode
                  : data.index_mode
                    ? " · " + data.index_mode
                    : ""
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
    assert data["platform_version"] == "0.39.0"
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
    assert raw["platform_version"] == "0.39.0"
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
```


学员须理解：Day 25 课件聚焦 txt MVP；仓库已向前兼容多格式，实验以 tests/day26 为准。

## _rebuild_index 与 _incremental_index

全量 rebuild 用于 Day 25 教学简单路径；Day 26 upload 可走 incremental（见仓库 `ingest_parsed(incremental=True)` 默认上传路径）。

衔接专节完。
