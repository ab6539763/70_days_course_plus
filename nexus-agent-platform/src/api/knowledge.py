"""
知识库 REST API — 文档上传与状态查询

需求：ZL-NA-REQ-025
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import KnowledgeStatusResponse, KnowledgeUploadResponse
from api.sessions import session_manager
from rag.ingestion import ingest_upload
from rag.knowledge_store import get_knowledge_store

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限


@router.get("/status", response_model=KnowledgeStatusResponse)
def knowledge_status() -> KnowledgeStatusResponse:
    """返回知识库文档数、分块数与文档列表"""
    store = get_knowledge_store()
    data = store.status_dict()
    return KnowledgeStatusResponse(**data)


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="UTF-8 文本文件 (.txt)"),
) -> KnowledgeUploadResponse:
    """
    上传企业文档到知识库：落盘 → 分块 → TF-IDF 索引 → 持久化 JSON。

    上传成功后清除服务端会话，使新对话使用更新后的检索索引。
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
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="仅支持 UTF-8 编码文本") from exc

    cleared = session_manager.clear_all()
    store = get_knowledge_store()

    return KnowledgeUploadResponse(
        filename=meta.name,
        chunk_count=meta.chunk_count,
        document_count=store.document_count,
        total_chunks=store.chunk_count,
        sessions_cleared=cleared,
        message="文档已入库，索引已更新",
    )
