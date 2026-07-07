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


class ChatResponse(BaseModel):
    """POST /api/chat 响应体 — 与 frontend/mock.js sendMessageApi 对齐"""

    reply: str
    meta: str = "API"
    kind: str = "llm"
    session_id: str


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
    message: str
