from __future__ import annotations

"""
Structured logging with structlog. TR: JSON formatlı loglama ve correlation id desteği.
"""

import logging
from typing import Any, Dict

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars
from fastapi import Request


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # TR: Correlation ID gibi contextvar alanlarını loglara ekle
            merge_contextvars,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger()


async def correlation_context(request: Request) -> Dict[str, Any]:
    # TR: Basit correlation id; header yoksa yeni bir tane üretilebilir
    cid = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
    return {"correlation_id": cid}


def bind_correlation_id(correlation_id: str | None) -> None:
    """TR: Correlation ID'yi structlog contextvars içine bağla."""
    if correlation_id:
        bind_contextvars(correlation_id=correlation_id)


def clear_correlation_context() -> None:
    """TR: İstek bitiminde context temizliği."""
    clear_contextvars()
