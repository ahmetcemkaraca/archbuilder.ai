"""
Enhanced authentication router with production-ready features:
- JWT token management with refresh tokens
- API key management with rotation
- Session management
- Role-based access control (RBAC)
- Multi-tenant security
- Comprehensive audit logging
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import envelope
from app.database.session import get_db
from app.database.models.auth_models import (
    ApiKey, ApiKeyStatus, User, UserRole, UserSession
)
from app.security.enhanced_auth import (
    ApiKeyManager, AuthenticationService, PasswordManager, TokenManager,
    get_current_active_user, get_current_user, log_audit_event, require_admin
)


router = APIRouter(prefix="/v1/auth", tags=["authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    role: UserRole = UserRole.USER
    organization_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    tenant_id: Optional[str] = None
    organization_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    permissions: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(None, gt=0, le=365)
    rate_limit_per_hour: Optional[int] = Field(None, gt=0)
    rate_limit_per_day: Optional[int] = Field(None, gt=0)
    allowed_ips: Optional[List[str]] = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str  # Only returned on creation
    key_prefix: str
    status: ApiKeyStatus
    permissions: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyInfoResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    status: ApiKeyStatus
    permissions: Optional[List[str]] = None
    usage_count: int
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class SessionResponse(BaseModel):
    id: str
    device_info: Optional[Dict[str, Any]] = None
    ip_address: str
    location: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header (nginx proxy)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


@router.post("/register", response_model=LoginResponse)
async def register(
    request: Request,
    user_data: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Register new user (admin only for production)"""
    
    # Only admins can create users in production
    if not settings.auth_dev_mode and (not current_user or current_user.role != UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for user creation"
        )
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    # Check if user already exists
    existing_user_query = select(User).where(User.email == user_data.email)
    result = await db.execute(existing_user_query)
    if result.scalar_one_or_none():
        await log_audit_event(
            db=db,
            event_type="user_registration",
            action="create",
            outcome="failure",
            ip_address=client_ip,
            user_agent=user_agent,
            error_message="Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    password_hash = PasswordManager.hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        organization_name=user_data.organization_name,
        is_verified=settings.auth_dev_mode  # Auto-verify in dev mode
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Log successful registration
    await log_audit_event(
        db=db,
        event_type="user_registration",
        action="create",
        outcome="success",
        user_id=new_user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"role": user_data.role.value}
    )
    
    return envelope(True, {
        "user": UserResponse(
            id=new_user.id,
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            role=new_user.role,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            tenant_id=new_user.tenant_id,
            organization_name=new_user.organization_name,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        ).dict(),
        "message": "User created successfully"
    })


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Enhanced login with session management and audit logging"""
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    auth_service = AuthenticationService(db)
    
    # Authenticate user
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        await log_audit_event(
            db=db,
            event_type="user_login",
            action="authenticate",
            outcome="failure",
            ip_address=client_ip,
            user_agent=user_agent,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create session
    session = await auth_service.create_user_session(
        user=user,
        ip_address=client_ip,
        user_agent=user_agent,
        device_info={"browser": user_agent}
    )
    
    # Create tokens
    access_token = TokenManager.create_access_token(
        subject=user.id,
        role=user.role,
        tenant_id=user.tenant_id,
        session_id=session.id
    )
    
    refresh_token_obj = await auth_service.create_refresh_token(
        user=user,
        session=session,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    refresh_token_string = TokenManager.create_refresh_token(user.id, session.id)
    
    # Log successful login
    await log_audit_event(
        db=db,
        event_type="user_login",
        action="authenticate",
        outcome="success",
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"session_id": session.id}
    )
    
    return envelope(True, {
        "access_token": access_token,
        "refresh_token": refresh_token_string,
        "token_type": "bearer",
        "expires_in": 3600,  # 1 hour
        "user": UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenant_id=user.tenant_id,
            organization_name=user.organization_name,
            created_at=user.created_at,
            last_login=user.last_login
        ).dict(),
        "session_id": session.id
    })


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Refresh access token using refresh token"""
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    auth_service = AuthenticationService(db)
    
    try:
        access_token, user = await auth_service.refresh_access_token(refresh_request.refresh_token)
        
        await log_audit_event(
            db=db,
            event_type="token_refresh",
            action="refresh",
            outcome="success",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return envelope(True, {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                tenant_id=user.tenant_id,
                organization_name=user.organization_name,
                created_at=user.created_at,
                last_login=user.last_login
            ).dict()
        })
        
    except HTTPException as e:
        await log_audit_event(
            db=db,
            event_type="token_refresh",
            action="refresh",
            outcome="failure",
            ip_address=client_ip,
            user_agent=user_agent,
            error_message=e.detail
        )
        raise e


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Logout user and end session"""
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    # Extract session_id from token (assuming it's in the token payload)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = TokenManager.decode_token(token)
            session_id = payload.get("session_id")
            
            if session_id:
                auth_service = AuthenticationService(db)
                await auth_service.logout_user(session_id)
        except Exception:
            pass  # Token might be invalid, but we still log the logout
    
    await log_audit_event(
        db=db,
        event_type="user_logout",
        action="logout",
        outcome="success",
        user_id=current_user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return envelope(True, {"message": "Logged out successfully"})


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get current user information"""
    
    return envelope(True, UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        tenant_id=current_user.tenant_id,
        organization_name=current_user.organization_name,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    ).dict())


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's active sessions"""
    
    query = select(UserSession).where(
        UserSession.user_id == current_user.id,
        UserSession.status == "active"
    ).order_by(UserSession.created_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    session_list = []
    for session in sessions:
        device_info = None
        if session.device_info:
            try:
                device_info = json.loads(session.device_info)
            except json.JSONDecodeError:
                pass
        
        session_list.append(SessionResponse(
            id=session.id,
            device_info=device_info,
            ip_address=session.ip_address,
            location=session.location,
            created_at=session.created_at,
            last_activity=session.last_activity,
            expires_at=session.expires_at
        ).dict())
    
    return envelope(True, {"sessions": session_list})


@router.post("/api-keys", response_model=Dict[str, Any])
async def create_api_key(
    request: Request,
    key_data: CreateApiKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create new API key for current user"""
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    # Generate API key
    api_key_string, key_hash, key_prefix = ApiKeyManager.generate_api_key()
    
    # Set expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = ApiKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        user_id=current_user.id,
        permissions=json.dumps(key_data.permissions) if key_data.permissions else None,
        expires_at=expires_at,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        rate_limit_per_day=key_data.rate_limit_per_day,
        allowed_ips=json.dumps(key_data.allowed_ips) if key_data.allowed_ips else None
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # Log API key creation
    await log_audit_event(
        db=db,
        event_type="api_key_created",
        action="create",
        outcome="success",
        user_id=current_user.id,
        resource=api_key.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"key_name": key_data.name, "key_prefix": key_prefix}
    )
    
    return envelope(True, ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=api_key_string,  # Only returned on creation
        key_prefix=key_prefix,
        status=api_key.status,
        permissions=key_data.permissions,
        expires_at=expires_at,
        created_at=api_key.created_at
    ).dict())


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """List user's API keys (without the actual key values)"""
    
    query = select(ApiKey).where(
        ApiKey.user_id == current_user.id
    ).order_by(ApiKey.created_at.desc())
    
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    key_list = []
    for key in api_keys:
        permissions = None
        if key.permissions:
            try:
                permissions = json.loads(key.permissions)
            except json.JSONDecodeError:
                pass
        
        key_list.append(ApiKeyInfoResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status,
            permissions=permissions,
            usage_count=key.usage_count,
            last_used=key.last_used,
            expires_at=key.expires_at,
            created_at=key.created_at
        ).dict())
    
    return envelope(True, {"api_keys": key_list})


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Revoke API key"""
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    
    # Find API key
    query = select(ApiKey).where(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user.id
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Revoke key
    api_key.status = ApiKeyStatus.REVOKED
    api_key.revoked_at = datetime.utcnow()
    
    await db.commit()
    
    # Log API key revocation
    await log_audit_event(
        db=db,
        event_type="api_key_revoked",
        action="delete",
        outcome="success",
        user_id=current_user.id,
        resource=api_key.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"key_name": api_key.name, "key_prefix": api_key.key_prefix}
    )
    
    return envelope(True, {"message": "API key revoked successfully"})