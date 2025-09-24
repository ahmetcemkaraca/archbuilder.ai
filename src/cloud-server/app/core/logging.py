from __future__ import annotations

"""
Structured logging with structlog. TR: JSON formatlı loglama ve correlation id desteği.
"""

import logging
from typing import Any, Dict

import structlog
from fastapi import Request


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
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


