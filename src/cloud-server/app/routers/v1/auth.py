from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import envelope
from app.security.authentication import create_access_token, create_api_key


router = APIRouter(prefix="/v1/auth", tags=["auth"])


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: AuthLoginRequest) -> Dict[str, Any]:
    # TR: Şimdilik dev modda herhangi bir kullanıcı kabul edilir; prod için DB kontrolü gerekir
    if not settings.auth_dev_mode:
        raise HTTPException(
            status_code=501, detail="Login not implemented for non-dev mode"
        )

    token = create_access_token(subject=body.email, expires_minutes=60)
    return envelope(
        True, {"access_token": token, "token_type": "bearer", "expires_in": 3600}
    )


class RefreshRequest(BaseModel):
    token: str = Field(..., description="Existing access or refresh token")


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(_: RefreshRequest) -> Dict[str, Any]:
    if not settings.auth_dev_mode:
        raise HTTPException(
            status_code=501, detail="Refresh not implemented for non-dev mode"
        )
    # TR: Basitçe yeni kısa ömürlü bir token üret
    token = create_access_token(subject="dev", expires_minutes=60)
    return envelope(
        True, {"access_token": token, "token_type": "bearer", "expires_in": 3600}
    )


class APIKeyResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


@router.post("/api-key", response_model=APIKeyResponse)
async def issue_api_key() -> Dict[str, Any]:
    if not settings.auth_dev_mode:
        raise HTTPException(
            status_code=501, detail="API key issuance not implemented for non-dev mode"
        )
    key = create_api_key()
    return envelope(True, {"api_key": key})
