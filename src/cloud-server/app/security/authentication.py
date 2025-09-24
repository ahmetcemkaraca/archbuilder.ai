from __future__ import annotations

"""
JWT issuance/validation and API key helpers.

Not: Kullanıcı ve DB modelleri henüz tanımlı değil; fonksiyonlar soyut tutuldu.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from app.core.config import settings


ALGORITHM = "HS256"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_secret_key() -> str:
    # TR: Env'den secret key; yoksa hata ver
    key = settings.jwt_secret or os.getenv("JWT_SECRET", None)
    if not key:
        raise RuntimeError("JWT_SECRET not configured")
    return key


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    now = datetime.now(tz=timezone.utc)
    to_encode: Dict[str, Any] = {"sub": subject, "iat": int(now.timestamp())}
    expire = now + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])


def create_api_key() -> str:
    return secrets.token_urlsafe(32)


async def get_api_key(x_api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    return x_api_key


async def require_api_key(api_key: Optional[str] = Depends(get_api_key)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    # TODO: DB doğrulaması ekle
    return api_key


