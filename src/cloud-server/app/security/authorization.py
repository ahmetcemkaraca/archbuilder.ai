from __future__ import annotations

"""
RBAC helpers and dependencies.
"""

from typing import Callable, Dict, Optional

from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.security.authentication import decode_token


class CurrentUser(Dict[str, object]):
    pass


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_dev_user: Optional[str] = Header(default=None),
    x_dev_role: Optional[str] = Header(default=None),
) -> CurrentUser:
    # TR: Dev modda header üzerinden kimlik sağlanabilir
    if settings.auth_dev_mode and (x_dev_user or x_dev_role):
        return CurrentUser({"id": x_dev_user or "dev", "role": x_dev_role or "user"})

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    claims = decode_token(token)
    role = claims.get("role") or claims.get("roles")
    sub = claims.get("sub")
    return CurrentUser({"id": sub, "role": role})


def require_roles(*roles: str) -> Callable[[CurrentUser], CurrentUser]:
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_role = (user.get("role") or "").lower() if user else ""
        allowed = {r.lower() for r in roles}
        if user_role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency


async def is_admin(user: CurrentUser = Depends(require_roles("admin"))) -> CurrentUser:
    return user


