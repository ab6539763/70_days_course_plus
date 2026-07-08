# ingestion 流水线精读

**需求**：ZL-NA-REQ-025 | **文件**：`rag/ingestion.py`

---

## 完整源码

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


---

## ingest_directory 批量路径

**L17-33**：遍历目录 `read_documents` → 逐文件 `ingest_text` → 最后统一 `save`。适合运维脚本初始化，非 API 热路径。

## ingest_upload API 路径（重点）

| 行号 | 代码 | 说明 |
|------|------|------|
| L51 | `safe_name = Path(filename).name` | 防止路径穿越 |
| L52-55 | `detect_format` | Day 26 扩展；Day 25 仅 .txt 通过 |
| L57-58 | `dest.write_bytes(data)` | 审计副本，rebuild 可重扫 |
| L59-63 | `kb.ingest_bytes` | 进入 KnowledgeStore |
| L64 | `kb.save()` | 持久化 |

## 异常映射

- `NexusError` → API 映射 400/500  
- `ValueError`（不支持格式）→ 422  
- `UnicodeDecodeError` → 400 UTF-8  

## 与 api/knowledge.py 衔接

```python
except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RewriteConfigResponse(**cfg.to_dict())


@router.post("/rewrite-preview", response_model=RewritePreviewResponse)
def rewrite_preview(body: RewritePreviewRequest) -> RewritePreviewResponse:
    """预览单条 query 的规则改写结果（不触发检索）"""
    store = get_knowledge_store()
    cfg = store.get_rewrite_config()
    rewriter = RuleBasedQueryRewriter(config=cfg)
    result = rewriter.rewrite(body.query)
    return RewritePreviewResponse(**result.to_dict())


@router.get("/citation-config", response_model=CitationConfigResponse)
def get_citation_config() -> CitationConfigResponse:
    """返回引用溯源开关与展示参数"""
    cfg = get_knowledge_store().get_citation_config()
    return CitationConfigResponse(**cfg.to_dict())


@router.put("/citation-config", response_model=CitationConfigResponse)
def update_citation_config(body: CitationConfigRequest) -> CitationConfigResponse:
    """更新引用溯源策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = CitationConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_citation_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CitationConfigResponse(**cfg.to_dict())


@router.post("/citation-preview", response_model=CitationPreviewResponse)
def citation_preview(body: CitationPreviewRequest) -> CitationPreviewResponse:
    """预览单条 query 的检索引用（含 rewrite / expansion 审计）"""
    store = get_knowledge_store()
    data = store.fetch_citations(body.query)
    return CitationPreviewResponse(**data)
```


上传路由不直接操作 Path，委托 `ingest_upload` 保持单一写入入口。

## 设计原则

**Single Writer**：所有上传必须经 `ingest_upload`，禁止 API 直接 `ingest_text` 绕过落盘。

精读完。


---

## 附录：constants 与样例（ingestion 专节）

```python
"""Day 25 常量"""

DAY = 25
REQ_ID = "ZL-NA-REQ-025"
PLATFORM_VERSION = "0.25.0"

SAMPLE_UPLOAD_NAME = "custom_faq.txt"
SAMPLE_UPLOAD_TEXT = """智链科技新产品 FAQ
Q: 最低起购金额是多少？
A: 最低起购金额为 1000 元。
Q: 赎回多久到账？
A: T+1 工作日到账。
投资有风险，入市需谨慎。
"""
```


`SAMPLE_UPLOAD_NAME` 用于 API 测试夹具文件名，内容含 FAQ 问答对，供 `test_chat_after_upload_uses_kb` 断言。

ingestion 附录完。

---

## 附录：ingest_directory 运维场景（ingestion vol2）

夜间批处理：`ingest_directory(Path("incoming"), pattern="*.txt")` 将运营 FTP 目录灌入 store。与 API upload 共享 `ingest_text` 内核，保证分块一致。

## 安全：safe_name

`Path("../../etc/passwd").name` → `passwd`，阻止目录穿越；但仍须病毒扫描（企业扩展）。

ingestion vol2 完。

---

## 单行注释作业

为 ingest_upload 每行写中文注释，提交 gist 链接可换贴纸。注释作业完。
