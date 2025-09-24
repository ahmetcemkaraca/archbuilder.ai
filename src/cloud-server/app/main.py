from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.routers.v1.rag import router as rag_router


def create_app() -> FastAPI:
    # Not: Logging/exception middleware P04-T2/T3 adımlarında eklenecek
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/health")
    async def health() -> Dict[str, Any]:  # TR: Basit sağlık kontrolü
        return {"status": "ok", "name": settings.app_name}

    # API routers
    app.include_router(rag_router)
    install_exception_handlers(app)
    return app


app = create_app()


