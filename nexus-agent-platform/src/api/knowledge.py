"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/chunk-config", response_model=ChunkConfigResponse)
def get_chunk_config() -> ChunkConfigResponse:
    """返回当前知识库默认分块参数"""
    cfg = get_knowledge_store().get_chunk_config()
    return ChunkConfigResponse(**cfg.to_dict())


@router.put("/chunk-config", response_model=ChunkConfigResponse)
def update_chunk_config(body: ChunkConfigRequest) -> ChunkConfigResponse:
    """更新默认分块参数（影响后续上传）"""
    store = get_knowledge_store()
    try:
        cfg = ChunkConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_chunk_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChunkConfigResponse(**cfg.to_dict())


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_chunk_configs(body: EvaluateRequest | None = None) -> EvaluateResponse:
    """
    对内置样例文档运行 A/B 分块评估，返回 hit@1 与推荐配置。

    默认使用 PRESET_CONFIGS 四套预设与 day27 评估问句集。
    """
    body = body or EvaluateRequest()
    if not _EVAL_SAMPLE.is_file():
        raise HTTPException(status_code=500, detail="评估样例文档缺失")

    doc = parse_bytes(_EVAL_SAMPLE.read_bytes(), _EVAL_SAMPLE.name)
    from day27.constants import EVAL_QUERIES

    queries = [EvalQuery.from_dict(q) for q in EVAL_QUERIES]

    if body.use_presets and not body.configs:
        configs = list(PRESET_CONFIGS)
    else:
        configs = [ChunkConfig.from_dict(c.model_dump()) for c in body.configs]
        for c in configs:
            c.validate()

    results = run_ab_experiment(doc, configs, queries)
    best = pick_best_config(results)
    if not best:
        raise HTTPException(status_code=500, detail="评估未产生结果")

    return EvaluateResponse(
        best_config=best.to_dict()["config"],
        results=[r.to_dict() for r in results],
        eval_query_count=len(queries),
    )


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild_knowledge_base(body: RebuildRequest | None = None) -> RebuildResponse:
    """
    按当前 chunk_config（或 evaluate 最优配置）全量重建知识库。

    重扫 sample_docs + knowledge_uploads，清空后重新分块与索引。
    """
    body = body or RebuildRequest()
    store = get_knowledge_store()

    if body.apply_best_config:
        if not _EVAL_SAMPLE.is_file():
            raise HTTPException(status_code=500, detail="评估样例文档缺失")
        report = rebuild_with_best_config(
            store,
            eval_sample_path=_EVAL_SAMPLE,
            include_sample_docs=body.include_sample_docs,
        )
    else:
        report = rebuild_store(store, include_sample_docs=body.include_sample_docs)

    cleared = session_manager.clear_all()
    data = report.to_dict()
    data["sessions_cleared"] = cleared
    return RebuildResponse(**data)


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
    上传企业文档到知识库：解析 → 落盘 → 分块 → Chroma 向量索引 → 持久化。

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
        index_mode=store.index_mode,
        message=f"文档已入库（{meta.format}），增量索引已更新",
    )
