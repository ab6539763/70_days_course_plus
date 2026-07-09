"""
知识库 REST API — 文档上传、分块调参与检索评估

需求：ZL-NA-REQ-025 / ZL-NA-REQ-026 / ZL-NA-REQ-027 / ZL-NA-REQ-028 / ZL-NA-REQ-029 / ZL-NA-REQ-030 / ZL-NA-REQ-031 / ZL-NA-REQ-032 / ZL-NA-REQ-033 / ZL-NA-REQ-034 / ZL-NA-REQ-035 / ZL-NA-REQ-036 / ZL-NA-REQ-037 / ZL-NA-REQ-038
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import (
    ChunkConfigRequest,
    ChunkConfigResponse,
    CitationConfigRequest,
    CitationConfigResponse,
    CitationPreviewRequest,
    CitationPreviewResponse,
    ExpansionConfigRequest,
    ExpansionConfigResponse,
    ExpansionPreviewRequest,
    ExpansionPreviewResponse,
    EvaluateRequest,
    EvaluateResponse,
    KnowledgeStatusResponse,
    KnowledgeUploadResponse,
    RebuildRequest,
    RebuildResponse,
    RerankConfigRequest,
    RerankConfigResponse,
    RewriteConfigRequest,
    RewriteConfigResponse,
    RewritePreviewRequest,
    RewritePreviewResponse,
    RouteConfigRequest,
    RouteConfigResponse,
    RoutePreviewRequest,
    RoutePreviewResponse,
    ValidationConfigRequest,
    ValidationConfigResponse,
    ValidationPreviewRequest,
    ValidationPreviewResponse,
    ValidationRetryPreviewRequest,
    ValidationRetryPreviewResponse,
    RetrievalConfigRequest,
    RetrievalConfigResponse,
)
from api.sessions import session_manager
from core.exceptions import NexusError, StorageError
from rag.chunk_config import PRESET_CONFIGS, ChunkConfig
from rag.ingestion import ingest_upload
from rag.knowledge_rebuild import rebuild_store, rebuild_with_best_config
from rag.knowledge_store import get_knowledge_store
from rag.citation_config import CitationConfig
from rag.expansion_config import ExpansionConfig
from rag.query_expander import build_expander
from rag.query_rewriter import RuleBasedQueryRewriter
from rag.query_router import RuleBasedQueryRouter
from rag.route_config import RouteConfig
from rag.validation_config import ValidationConfig
from rag.rerank_config import RerankConfig
from rag.rewrite_config import RewriteConfig
from rag.retrieval_config import RetrievalConfig
from rag.retrieval_eval import EvalQuery, pick_best_config, run_ab_experiment
from tools.doc_parser import parse_bytes

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 512_000  # 500 KB 教学上限
_EVAL_SAMPLE = (
    Path(__file__).resolve().parent.parent / "day26" / "sample_docs" / "product_notice.md"
)


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
def get_retrieval_config() -> RetrievalConfigResponse:
    """返回当前检索模式（vector / keyword / hybrid）与融合参数"""
    cfg = get_knowledge_store().get_retrieval_config()
    return RetrievalConfigResponse(**cfg.to_dict())


@router.put("/retrieval-config", response_model=RetrievalConfigResponse)
def update_retrieval_config(body: RetrievalConfigRequest) -> RetrievalConfigResponse:
    """更新检索策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RetrievalConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_retrieval_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RetrievalConfigResponse(**cfg.to_dict())


@router.get("/rerank-config", response_model=RerankConfigResponse)
def get_rerank_config() -> RerankConfigResponse:
    """返回 rerank 开关、候选池大小与模型标识"""
    cfg = get_knowledge_store().get_rerank_config()
    return RerankConfigResponse(**cfg.to_dict())


@router.put("/rerank-config", response_model=RerankConfigResponse)
def update_rerank_config(body: RerankConfigRequest) -> RerankConfigResponse:
    """更新 rerank 策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RerankConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rerank_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RerankConfigResponse(**cfg.to_dict())


@router.get("/rewrite-config", response_model=RewriteConfigResponse)
def get_rewrite_config() -> RewriteConfigResponse:
    """返回查询改写开关与规则模式"""
    cfg = get_knowledge_store().get_rewrite_config()
    return RewriteConfigResponse(**cfg.to_dict())


@router.put("/rewrite-config", response_model=RewriteConfigResponse)
def update_rewrite_config(body: RewriteConfigRequest) -> RewriteConfigResponse:
    """更新查询改写策略；变更后清除 RAG 缓存"""
    store = get_knowledge_store()
    try:
        cfg = RewriteConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_rewrite_config(cfg)
        store.save()
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


@router.get("/expansion-config", response_model=ExpansionConfigResponse)
def get_expansion_config() -> ExpansionConfigResponse:
    """返回多 query 扩展开关与参数"""
    cfg = get_knowledge_store().get_expansion_config()
    return ExpansionConfigResponse(**cfg.to_dict())


@router.put("/expansion-config", response_model=ExpansionConfigResponse)
def update_expansion_config(body: ExpansionConfigRequest) -> ExpansionConfigResponse:
    """更新多 query 扩展策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = ExpansionConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_expansion_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExpansionConfigResponse(**cfg.to_dict())


@router.post("/expansion-preview", response_model=ExpansionPreviewResponse)
def expansion_preview(body: ExpansionPreviewRequest) -> ExpansionPreviewResponse:
    """预览单条 query 的多路扩展结果"""
    store = get_knowledge_store()
    cfg = store.get_expansion_config()
    expander = build_expander(cfg)
    result = expander.expand(body.query)
    return ExpansionPreviewResponse(**result.to_dict())


@router.get("/route-config", response_model=RouteConfigResponse)
def get_route_config() -> RouteConfigResponse:
    """返回检索管线路由开关与默认意图"""
    cfg = get_knowledge_store().get_route_config()
    return RouteConfigResponse(**cfg.to_dict())


@router.put("/route-config", response_model=RouteConfigResponse)
def update_route_config(body: RouteConfigRequest) -> RouteConfigResponse:
    """更新检索管线路由策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = RouteConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_route_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RouteConfigResponse(**cfg.to_dict())


@router.post("/route-preview", response_model=RoutePreviewResponse)
def route_preview(body: RoutePreviewRequest) -> RoutePreviewResponse:
    """预览单条 query 的路由决策（expand/rewrite 开关）"""
    store = get_knowledge_store()
    cfg = store.get_route_config()
    router = RuleBasedQueryRouter(config=cfg)
    result = router.route(body.query)
    return RoutePreviewResponse(**result.to_dict())


@router.get("/validation-config", response_model=ValidationConfigResponse)
def get_validation_config() -> ValidationConfigResponse:
    """返回答案校验开关与阈值"""
    cfg = get_knowledge_store().get_validation_config()
    return ValidationConfigResponse(**cfg.to_dict())


@router.put("/validation-config", response_model=ValidationConfigResponse)
def update_validation_config(body: ValidationConfigRequest) -> ValidationConfigResponse:
    """更新答案校验策略并持久化"""
    store = get_knowledge_store()
    try:
        cfg = ValidationConfig.from_dict(body.model_dump())
        cfg.validate()
        store.set_validation_config(cfg)
        store.save()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ValidationConfigResponse(**cfg.to_dict())


@router.post("/validation-preview", response_model=ValidationPreviewResponse)
def validation_preview(body: ValidationPreviewRequest) -> ValidationPreviewResponse:
    """预览单条 query + reply 的引用一致性校验"""
    from rag.answer_validator import RuleBasedAnswerValidator

    store = get_knowledge_store()
    citations = list(body.citations)
    if not citations:
        cite_data = store.fetch_citations(body.query)
        citations = cite_data.get("citations") or []
    cfg = store.get_validation_config()
    preview_cfg = ValidationConfig.from_dict({**cfg.to_dict(), "enabled": True})
    result = RuleBasedAnswerValidator(config=preview_cfg).validate(
        body.query, body.reply, citations
    )
    return ValidationPreviewResponse(**result.to_dict())


@router.post("/validation-retry-preview", response_model=ValidationRetryPreviewResponse)
def validation_retry_preview(
    body: ValidationRetryPreviewRequest,
) -> ValidationRetryPreviewResponse:
    """模拟校验失败后的 rag_wide 重检索与再校验"""
    from rag.validation_retry import apply_validation_retry

    store = get_knowledge_store()
    cite_data = store.fetch_citations(body.query)
    citations = list(body.citations) or cite_data.get("citations") or []
    if body.citations:
        cite_data = {**cite_data, "citations": citations}

    saved = store.get_validation_config()
    retry_cfg = ValidationConfig.from_dict(
        {**saved.to_dict(), "enabled": True, "retry_on_fail": True, "max_retries": 1}
    )
    store.set_validation_config(retry_cfg)
    try:
        outcome = apply_validation_retry(
            store,
            body.query,
            body.reply,
            citations,
            cite_data,
        )
    finally:
        store.set_validation_config(saved)

    if outcome is None:
        raise HTTPException(status_code=400, detail="校验已关闭")
    payload = outcome.validation.to_dict()
    payload["retry_route"] = outcome.cite_data.get("route")
    return ValidationRetryPreviewResponse(**payload)


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
