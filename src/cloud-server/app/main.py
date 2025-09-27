from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.enhanced_security import EnhancedSecurityMiddleware
from app.core.rate_limit import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.routers.v1.rag import router as rag_router
from app.routers.v1.auth import router as auth_router
from app.routers.v1.enhanced_auth import router as enhanced_auth_router
from app.routers.v1.storage import router as storage_router
from app.routers.v1.ai import router as ai_router
from app.routers.v1.websocket import router as websocket_router
from app.routers.v1.regional import router as regional_router


def create_app() -> FastAPI:
    # Configure logging first
    configure_logging(settings.log_level)
    logger = get_logger()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="ArchBuilder.AI Cloud Server - AI-powered architectural design platform",
        version="1.2.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None
    )
    
    # Add enhanced security middleware (order matters - most restrictive first)
    app.add_middleware(EnhancedSecurityMiddleware)  # Comprehensive security checks
    app.add_middleware(TenantIsolationMiddleware)   # Multi-tenant isolation
    app.add_middleware(RateLimitingMiddleware)      # Rate limiting
    app.add_middleware(RequestIdMiddleware)         # Request correlation
    app.add_middleware(SecurityHeadersMiddleware)   # Security headers
    app.add_middleware(SlowAPIMiddleware)           # Rate limiting integration
    app.state.limiter = limiter

    @app.get("/health")
    async def health() -> Dict[str, Any]:  # TR: Basit sağlık kontrolü
        return {"status": "ok", "name": settings.app_name}

    # API routers
    # Add startup event for secret rotation
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        try:
            # Setup secret rotation if enabled
            if settings.environment == "production":
                await setup_secret_rotation()
            
            logger.info(f"ArchBuilder.AI Cloud Server started - Environment: {settings.environment}")
            
        except Exception as e:
            logger.error(f"Startup initialization failed: {e}")

    # API routers
    app.include_router(rag_router)
    app.include_router(auth_router)
    app.include_router(enhanced_auth_router)
    app.include_router(storage_router)
    app.include_router(ai_router)
    app.include_router(websocket_router)
    app.include_router(regional_router)
    install_exception_handlers(app)
    
    return app


app = create_app()
