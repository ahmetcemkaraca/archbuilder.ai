from __future__ import annotations

"""
Security headers middleware (CSP/HSTS, etc.).
"""

from typing import List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._headers: List[Tuple[bytes, bytes]] = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload"),
            (b"x-permitted-cross-domain-policies", b"none"),
            (b"content-security-policy", b"default-src 'self'; frame-ancestors 'none'; object-src 'none'")
        ]

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        for k, v in self._headers:
            response.headers.append(k.decode("utf-8"), v.decode("utf-8"))
        return response


