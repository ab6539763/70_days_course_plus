"""
知识库 REST API — 文档上传与状态查询

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import KnowledgeStatusResponse, KnowledgeUploadResponse
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.ingestion import ingest_upload
from rag.knowledge_store import get_knowledge_store

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限


@router.get("/status", response_model=KnowledgeStatusResponse)
def knowledge_status() -> KnowledgeStatusResponse:
    """返回知识库文档数、分块数、支持格式与文档列表"""
    store = get_knowledge_store()
    data = store.status_dict()
    return KnowledgeStatusResponse(**data)


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="企业文档 (.txt / .md / .pdf)"),
) -> KnowledgeUploadResponse:
    """
    上传企业文档到知识库：解析 → 落盘 → 分块 → TF-IDF 索引 → 持久化 JSON。

    Day 26 起支持 Markdown 与 PDF。上传成功后清除服务端会话。
    """
    if not file.filename:
        raise HTTPException(status_code=422, detail="缺少文件名")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 500KB 上限")

    try:
        meta = ingest_upload(data, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NexusError as exc:
        status = 400 if exc.code in (
            "PDF_PARSE_ERROR", "PDF_EMPTY", "UNSUPPORTED_FORMAT", "EMPTY_FILE"
        ) else 500
        raise HTTPException(status_code=status, detail=exc.message) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文本文件须为 UTF-8 编码") from exc

    cleared = session_manager.clear_all()
    store = get_knowledge_store()

    return KnowledgeUploadResponse(
        filename=meta.name,
        format=meta.format,
        chunk_count=meta.chunk_count,
        document_count=store.document_count,
        total_chunks=store.chunk_count,
        sessions_cleared=cleared,
        message=f"文档已入库（{meta.format}），索引已更新",
    )
