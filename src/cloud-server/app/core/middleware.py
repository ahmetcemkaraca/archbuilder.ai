from __future__ import annotations

"""
Request/response middleware: request id ve basit access log.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response

from .logging import get_logger, bind_correlation_id, clear_correlation_context


class RequestIdMiddleware:
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        self.app = app

    async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # TR: Correlation ID'yi global log context'ine bağla
        bind_correlation_id(request_id)
        start = time.perf_counter()
        logger = get_logger().bind(
            request_id=request_id, path=request.url.path, method=request.method
        )

        async def send_wrapper(message):  # type: ignore[no-untyped-def]
            if message.get("type") == "http.response.start":
                # TR: Yanıta hem X-Correlation-ID hem X-Request-ID yazalım
                headers = [
                    (b"x-correlation-id", request_id.encode("utf-8")),
                    (b"x-request-id", request_id.encode("utf-8")),
                ]
                existing = message.get("headers") or []
                message["headers"] = list(existing) + headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info("request_ok", duration_ms=duration_ms)
        except Exception as exc:  # noqa: BLE001
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error("request_error", duration_ms=duration_ms, error=str(exc))
            raise
        finally:
            # TR: Context temizliği
            clear_correlation_context()
