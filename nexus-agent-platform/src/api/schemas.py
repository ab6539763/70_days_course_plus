"""
API 请求/响应模型 — Pydantic v2

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/chat 请求体"""

    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: str | None = Field(
        default=None,
        max_length=64,
        description="会话 ID，省略则使用 default",
    )
    agent_mode: bool = Field(
        default=False,
        description="为 true 时走 ReAct Agent 工具链（Day 39）",
    )


class ChatResponse(BaseModel):
    """POST /api/chat 响应体 — 与 frontend/mock.js sendMessageApi 对齐"""

    reply: str
    meta: str = "API"
    kind: str = "llm"
    session_id: str
    citations: list[dict] = Field(default_factory=list)
    rewrite: dict | None = None
    expansion: dict | None = None
    route: dict | None = None
    validation: dict | None = None
    agent_trace: list[dict] | None = None
    tools_used: list[str] | None = None


class HealthResponse(BaseModel):
    """GET /api/health"""

    status: str = "ok"
    version: str
    mock_llm: bool


class ErrorResponse(BaseModel):
    """统一错误响应"""

    detail: str
    code: str = "ERROR"


class SessionResetRequest(BaseModel):
    """POST /api/session/reset"""

    session_id: str = Field(..., min_length=1, max_length=64)


class SessionResetResponse(BaseModel):
    """会话重置结果"""

    session_id: str
    cleared: bool


class KnowledgeStatusResponse(BaseModel):
    """GET /api/knowledge/status"""

    document_count: int
    chunk_count: int
    documents: list[dict]
    store_path: str | None = None
    platform_version: str
    supported_formats: list[dict] = Field(default_factory=list)
    chunk_config: dict = Field(default_factory=dict)
    last_rebuilt_at: str | None = None
    last_incremental_at: str | None = None
    index_mode: str = "full"
    vector_backend: str = "chroma"
    chroma_path: str | None = None
    chroma_count: int = 0
    retrieval_config: dict = Field(default_factory=dict)
    rerank_config: dict = Field(default_factory=dict)
    rewrite_config: dict = Field(default_factory=dict)
    citation_config: dict = Field(default_factory=dict)
    expansion_config: dict = Field(default_factory=dict)
    route_config: dict = Field(default_factory=dict)
    validation_config: dict = Field(default_factory=dict)
    react_config: dict = Field(default_factory=dict)


class RetrievalConfigRequest(BaseModel):
    """PUT /api/knowledge/retrieval-config"""

    mode: str = Field("hybrid", pattern="^(vector|keyword|hybrid)$")
    keyword_weight: float = Field(0.35, ge=0.0, le=1.0)
    vector_weight: float = Field(0.65, ge=0.0, le=1.0)
    fusion: str = Field("weighted", pattern="^(weighted|rrf)$")
    rrf_k: int = Field(60, ge=1, le=500)


class RetrievalConfigResponse(BaseModel):
    mode: str
    keyword_weight: float
    vector_weight: float
    fusion: str
    rrf_k: int


class RerankConfigRequest(BaseModel):
    """PUT /api/knowledge/rerank-config"""

    enabled: bool = True
    candidate_pool: int = Field(20, ge=1, le=100)
    model: str = Field("mock", pattern="^mock$")


class RerankConfigResponse(BaseModel):
    enabled: bool
    candidate_pool: int
    model: str


class RewriteConfigRequest(BaseModel):
    """PUT /api/knowledge/rewrite-config"""

    enabled: bool = True
    mode: str = Field("rules", pattern="^rules$")
    fallback_to_original: bool = True
    max_rewrite_len: int = Field(200, ge=10, le=500)


class RewriteConfigResponse(BaseModel):
    enabled: bool
    mode: str
    fallback_to_original: bool
    max_rewrite_len: int


class RewritePreviewRequest(BaseModel):
    """POST /api/knowledge/rewrite-preview"""

    query: str = Field(..., min_length=1, max_length=500)


class RewritePreviewResponse(BaseModel):
    original: str
    rewritten: str
    changed: bool
    rule_id: str | None = None


class CitationConfigRequest(BaseModel):
    """PUT /api/knowledge/citation-config"""

    enabled: bool = True
    max_citations: int = Field(3, ge=1, le=10)
    preview_max_chars: int = Field(120, ge=20, le=500)
    include_rewrite_meta: bool = True
    include_expansion_meta: bool = True
    include_route_meta: bool = True


class CitationConfigResponse(BaseModel):
    enabled: bool
    max_citations: int
    preview_max_chars: int
    include_rewrite_meta: bool
    include_expansion_meta: bool
    include_route_meta: bool


class CitationPreviewRequest(BaseModel):
    """POST /api/knowledge/citation-preview"""

    query: str = Field(..., min_length=1, max_length=500)


class CitationPreviewResponse(BaseModel):
    query: str
    citations: list[dict]
    rewrite: dict | None = None
    expansion: dict | None = None
    route: dict | None = None


class ExpansionConfigRequest(BaseModel):
    """PUT /api/knowledge/expansion-config"""

    enabled: bool = True
    mode: str = Field("templates", pattern="^(templates|hyde_mock)$")
    max_queries: int = Field(4, ge=1, le=8)
    include_original: bool = True
    per_query_top_k: int = Field(5, ge=1, le=20)


class ExpansionConfigResponse(BaseModel):
    enabled: bool
    mode: str
    max_queries: int
    include_original: bool
    per_query_top_k: int


class ExpansionPreviewRequest(BaseModel):
    """POST /api/knowledge/expansion-preview"""

    query: str = Field(..., min_length=1, max_length=500)


class ExpansionPreviewResponse(BaseModel):
    original: str
    queries: list[str]
    changed: bool
    mode: str
    rule_id: str | None = None


class RouteConfigRequest(BaseModel):
    """PUT /api/knowledge/route-config"""

    enabled: bool = True
    mode: str = Field("rules", pattern="^rules$")
    fallback_intent: str = Field(
        "rag_standard",
        pattern="^(faq_fast|rag_standard|rag_wide)$",
    )


class RouteConfigResponse(BaseModel):
    enabled: bool
    mode: str
    fallback_intent: str


class RoutePreviewRequest(BaseModel):
    """POST /api/knowledge/route-preview"""

    query: str = Field(..., min_length=1, max_length=500)


class RoutePreviewResponse(BaseModel):
    original: str
    intent: str
    expand: bool
    rewrite: bool
    rule_id: str | None = None
    confidence: float
    label: str


class ValidationConfigRequest(BaseModel):
    """PUT /api/knowledge/validation-config"""

    enabled: bool = True
    mode: str = Field("overlap", pattern="^(overlap|strict)$")
    min_score: float = Field(0.35, ge=0.0, le=1.0)
    refuse_on_fail: bool = True
    retry_on_fail: bool = False
    max_retries: int = Field(1, ge=0, le=3)


class ValidationConfigResponse(BaseModel):
    enabled: bool
    mode: str
    min_score: float
    refuse_on_fail: bool
    retry_on_fail: bool
    max_retries: int


class ValidationPreviewRequest(BaseModel):
    """POST /api/knowledge/validation-preview"""

    query: str = Field(..., min_length=1, max_length=500)
    reply: str = Field(..., min_length=1, max_length=4000)
    citations: list[dict] = Field(default_factory=list)


class ValidationPreviewResponse(BaseModel):
    query: str
    reply: str
    passed: bool
    score: float
    reason: str
    citation_coverage: float
    matched_citation_ranks: list[int]
    refused: bool = False
    retries: int = 0


class ValidationRetryPreviewRequest(BaseModel):
    """POST /api/knowledge/validation-retry-preview"""

    query: str = Field(..., min_length=1, max_length=500)
    reply: str = Field(..., min_length=1, max_length=4000)
    citations: list[dict] = Field(default_factory=list)


class ValidationRetryPreviewResponse(BaseModel):
    query: str
    reply: str
    passed: bool
    score: float
    reason: str
    citation_coverage: float
    matched_citation_ranks: list[int]
    refused: bool = False
    retries: int = 0
    retry_route: dict | None = None


class ReactConfigRequest(BaseModel):
    """PUT /api/agent/react-config"""

    enabled: bool = True
    max_steps: int = Field(3, ge=1, le=8)
    use_session_history: bool = True
    mock_planner: bool = True


class ReactConfigResponse(BaseModel):
    enabled: bool
    max_steps: int
    use_session_history: bool
    mock_planner: bool


class ReactPreviewRequest(BaseModel):
    """POST /api/agent/react-preview"""

    query: str = Field(..., min_length=1, max_length=500)
    history: list[str] = Field(default_factory=list)


class ReactPreviewResponse(BaseModel):
    query: str
    reply: str
    steps: list[dict]
    tools_used: list[str]


class RebuildRequest(BaseModel):
    """POST /api/knowledge/rebuild"""

    include_sample_docs: bool = True
    apply_best_config: bool = False


class RebuildResponse(BaseModel):
    """全量重建结果"""

    documents_before: int
    chunks_before: int
    documents_after: int
    chunks_after: int
    sources_processed: int
    chunk_config: dict
    source_files: list[str]
    rebuilt_at: str
    sessions_cleared: int
    message: str


class ChunkConfigRequest(BaseModel):
    """PUT /api/knowledge/chunk-config"""

    chunk_size: int = Field(200, ge=50, le=2000)
    overlap: int = Field(40, ge=0, le=500)
    strategy: str = Field("auto", pattern="^(auto|fixed|markdown)$")
    name: str = Field("default", max_length=32)


class ChunkConfigResponse(BaseModel):
    chunk_size: int
    overlap: int
    strategy: str
    name: str


class EvaluateRequest(BaseModel):
    """POST /api/knowledge/evaluate — 可选自定义配置列表"""

    use_presets: bool = True
    configs: list[ChunkConfigRequest] = Field(default_factory=list)


class EvaluateResponse(BaseModel):
    best_config: dict
    results: list[dict]
    eval_query_count: int


class KnowledgeUploadResponse(BaseModel):
    """POST /api/knowledge/upload"""

    filename: str
    format: str = "txt"
    chunk_count: int
    document_count: int
    total_chunks: int
    sessions_cleared: int
    index_mode: str = "incremental"
    message: str
