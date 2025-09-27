from __future__ import annotations

"""
Global exception handlers, custom exceptions and standard response envelope.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


# Custom Exception Classes
class ArchBuilderError(Exception):
    """Base exception class for ArchBuilder.AI"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class ValidationError(ArchBuilderError):
    """Validation hatası"""


class ProcessingError(ArchBuilderError):
    """İşlem hatası"""


class AIServiceError(ArchBuilderError):
    """AI servis hatası"""


class CADProcessingError(ArchBuilderError):
    """CAD dosya işleme hatası"""


class ConfigurationError(ArchBuilderError):
    """Konfigürasyon hatası"""


class AuthenticationError(ArchBuilderError):
    """Kimlik doğrulama hatası"""


class AuthorizationError(ArchBuilderError):
    """Yetkilendirme hatası"""


class DatabaseError(ArchBuilderError):
    """Veritabanı hatası"""


class NetworkError(ArchBuilderError):
    """Ağ bağlantısı hatası"""


class RateLimitError(ArchBuilderError):
    """Rate limit aşım hatası"""


class ReviewServiceError(ArchBuilderError):
    """Human review service hatası"""


class LayoutGenerationError(ArchBuilderError):
    """Layout generation hatası"""


def envelope(
    success: bool, data: Any | None = None, error: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    return {"success": success, "data": data, "error": error}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exc_handler(
        _: Request, exc: HTTPException
    ) -> JSONResponse:  # noqa: D401
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope(False, None, {"message": exc.detail}),
        )

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(
        _: Request, exc: Exception
    ) -> JSONResponse:  # noqa: D401
        return JSONResponse(
            status_code=500, content=envelope(False, None, {"message": str(exc)})
        )
