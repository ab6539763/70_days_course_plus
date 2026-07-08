"""
FastAPI 应用入口 — 挂载 API 与 frontend 静态资源

运行：
    cd nexus-agent-platform
    PYTHONPATH=src NEXUS_LLM_MOCK=1 uvicorn api.app:app --reload --port 8000

需求：ZL-NA-REQ-023
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.chat import router as chat_router
from api.knowledge import router as knowledge_router
from core.exceptions import APIError, ConfigError, ModelValidationError, NexusError

# nexus-agent-platform/src/api/app.py → 仓库根 frontend/
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FRONTEND_DIR = _REPO_ROOT / "frontend"


def create_app(*, enable_cors: bool = True) -> FastAPI:
    app = FastAPI(
        title="NexusAgent API",
        description="智链科技灵犀智能体平台 — Sprint 3 Chat API",
        version="0.32.0",
    )

    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(chat_router)
    app.include_router(knowledge_router)

    @app.exception_handler(ModelValidationError)
    async def validation_handler(_request: Request, exc: ModelValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(ConfigError)
    async def config_handler(_request: Request, exc: ConfigError):
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(APIError)
    async def api_handler(_request: Request, exc: APIError):
        return JSONResponse(
            status_code=502,
            content={"detail": exc.message, "code": exc.code},
        )

    if _FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

    return app


app = create_app()
