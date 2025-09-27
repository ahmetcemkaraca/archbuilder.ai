from __future__ import annotations

"""
Global exception handlers and standard response envelope.
"""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class AuthenticationError(Exception):
    """Authentication related errors"""
    pass


class AuthorizationError(Exception):
    """Authorization related errors"""
    pass


def envelope(success: bool, data: Any | None = None, error: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"success": success, "data": data, "error": error}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exc_handler(_: Request, exc: HTTPException) -> JSONResponse:  # noqa: D401
        return JSONResponse(status_code=exc.status_code, content=envelope(False, None, {"message": exc.detail}))

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(_: Request, exc: Exception) -> JSONResponse:  # noqa: D401
        return JSONResponse(status_code=500, content=envelope(False, None, {"message": str(exc)}))


