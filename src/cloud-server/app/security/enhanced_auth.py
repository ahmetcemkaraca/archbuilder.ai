"""
Enhanced production authentication service for ArchBuilder.AI.
Includes JWT token management, API key handling, session management, and RBAC.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update

from app.core.config import settings
from app.database.session import get_db
from app.database.models.auth_models import (
    ApiKey, ApiKeyStatus, AuditLog, RefreshToken, User, UserRole, UserSession, SessionStatus
)
from app.core.exceptions import AuthenticationError, AuthorizationError


ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 1
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
API_KEY_PREFIX = "ab_key_"

# FastAPI security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class SecretManager:
    """Manages secrets with fallback to environment variables"""
    
    @staticmethod
    def get_jwt_secret() -> str:
        """Get JWT secret key from secure storage or environment"""
        # TODO: Implement HashiCorp Vault integration
        secret_key = settings.jwt_secret
        if not secret_key:
            raise RuntimeError("JWT_SECRET not configured")
        return secret_key
    
    @staticmethod
    def get_api_key_secret() -> str:
        """Get API key secret for hashing"""
        # TODO: Implement HashiCorp Vault integration
        return settings.jwt_secret or "default-api-key-secret"


class PasswordManager:
    """Secure password handling utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class TokenManager:
    """JWT token creation and validation"""
    
    @staticmethod
    def create_access_token(
        subject: str,
        role: UserRole,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with enhanced claims"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode = {
            "sub": subject,  # user_id
            "role": role.value,
            "exp": expire.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "type": "access",
            "session_id": session_id
        }
        
        if tenant_id:
            to_encode["tenant_id"] = tenant_id
        
        if permissions:
            to_encode["permissions"] = permissions
        
        return jwt.encode(to_encode, SecretManager.get_jwt_secret(), algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(subject: str, session_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": subject,
            "session_id": session_id,
            "exp": expire.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "type": "refresh"
        }
        
        return jwt.encode(to_encode, SecretManager.get_jwt_secret(), algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, SecretManager.get_jwt_secret(), algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def validate_token_type(payload: Dict[str, Any], expected_type: str) -> None:
        """Validate token type"""
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationError(f"Invalid token type: expected {expected_type}, got {token_type}")


class ApiKeyManager:
    """API key generation, validation, and management"""
    
    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """Generate new API key and return (key, hash, prefix)"""
        # Generate random key
        key_suffix = secrets.token_urlsafe(32)
        full_key = f"{API_KEY_PREFIX}{key_suffix}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Create prefix for identification (first 12 chars)
        key_prefix = full_key[:12]
        
        return full_key, key_hash, key_prefix
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def validate_api_key(
        api_key: str,
        db: AsyncSession
    ) -> Optional[ApiKey]:
        """Validate API key and return key object if valid"""
        key_hash = ApiKeyManager.hash_api_key(api_key)
        
        query = select(ApiKey).options(
            selectinload(ApiKey.user)
        ).where(
            ApiKey.key_hash == key_hash,
            ApiKey.status == ApiKeyStatus.ACTIVE
        )
        
        result = await db.execute(query)
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj:
            return None
        
        # Check expiration
        if api_key_obj.is_expired:
            # Mark as expired
            await db.execute(
                update(ApiKey)
                .where(ApiKey.id == api_key_obj.id)
                .values(status=ApiKeyStatus.EXPIRED)
            )
            await db.commit()
            return None
        
        # Update usage statistics
        await db.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key_obj.id)
            .values(
                usage_count=ApiKey.usage_count + 1,
                last_used=datetime.utcnow()
            )
        )
        await db.commit()
        
        return api_key_obj


class AuthenticationService:
    """Main authentication service with RBAC and session management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Verify password
        if not PasswordManager.verify_password(password, user.password_hash):
            # Increment login attempts
            await self._handle_failed_login(user)
            return None
        
        # Check if user can login
        if not user.can_login():
            return None
        
        # Reset login attempts on successful login
        await self._handle_successful_login(user)
        
        return user
    
    async def create_user_session(
        self,
        user: User,
        ip_address: str,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Create new user session"""
        session = UserSession(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=json.dumps(device_info) if device_info else None,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def create_refresh_token(
        self,
        user: User,
        session: UserSession,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Create refresh token"""
        # Generate refresh token
        token_string = TokenManager.create_refresh_token(user.id, session.id)
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()
        
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user.id,
            session_id=session.id,
            expires_at=datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            issued_ip=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(refresh_token)
        await self.db.commit()
        
        return refresh_token
    
    async def refresh_access_token(self, refresh_token_string: str) -> tuple[str, User]:
        """Refresh access token using refresh token"""
        try:
            payload = TokenManager.decode_token(refresh_token_string)
            TokenManager.validate_token_type(payload, "refresh")
        except AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload["sub"]
        session_id = payload["session_id"]
        
        # Hash the token to find in database
        token_hash = hashlib.sha256(refresh_token_string.encode()).hexdigest()
        
        query = select(RefreshToken).options(
            selectinload(RefreshToken.user),
            selectinload(RefreshToken.session)
        ).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.session_id == session_id
        )
        
        result = await self.db.execute(query)
        refresh_token = result.scalar_one_or_none()
        
        if not refresh_token or not refresh_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Check if session is still active
        if not refresh_token.session or not refresh_token.session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        # Update token usage
        refresh_token.used_at = datetime.utcnow()
        await self.db.commit()
        
        # Create new access token
        access_token = TokenManager.create_access_token(
            subject=refresh_token.user.id,
            role=refresh_token.user.role,
            tenant_id=refresh_token.user.tenant_id,
            session_id=session_id
        )
        
        return access_token, refresh_token.user
    
    async def logout_user(self, session_id: str) -> None:
        """Logout user by ending session"""
        # End session
        await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(
                status=SessionStatus.EXPIRED,
                ended_at=datetime.utcnow()
            )
        )
        
        # Revoke all refresh tokens for this session
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id)
            .values(
                is_revoked=True,
                revoked_at=datetime.utcnow()
            )
        )
        
        await self.db.commit()
    
    async def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt"""
        user.login_attempts += 1
        
        # Lock user after 5 failed attempts
        if user.login_attempts >= 5:
            user.is_locked = True
            user.lockout_until = datetime.utcnow() + timedelta(minutes=30)
        
        await self.db.commit()
    
    async def _handle_successful_login(self, user: User) -> None:
        """Handle successful login"""
        user.login_attempts = 0
        user.is_locked = False
        user.lockout_until = None
        user.last_login = datetime.utcnow()
        
        await self.db.commit()


# Dependency functions for FastAPI
async def get_current_user_from_token(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token"""
    if not token:
        return None
    
    try:
        payload = TokenManager.decode_token(token)
        TokenManager.validate_token_type(payload, "access")
    except AuthenticationError:
        return None
    
    user_id = payload["sub"]
    session_id = payload.get("session_id")
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return None
    
    # Verify session if present
    if session_id:
        session_query = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session or not session.is_active:
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        await db.commit()
    
    return user


async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from API key"""
    if not api_key:
        return None
    
    api_key_obj = await ApiKeyManager.validate_api_key(api_key, db)
    if not api_key_obj:
        return None
    
    return api_key_obj.user


async def get_current_user(
    user_from_token: Optional[User] = Depends(get_current_user_from_token),
    user_from_api_key: Optional[User] = Depends(get_current_user_from_api_key)
) -> User:
    """Get current authenticated user (from token or API key)"""
    user = user_from_token or user_from_api_key
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.value} required"
            )
        return current_user
    
    return role_checker


def require_admin():
    """Dependency to require admin role"""
    return require_role(UserRole.ADMIN)


async def log_audit_event(
    db: AsyncSession,
    event_type: str,
    action: str,
    outcome: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    ip_address: str = "unknown",
    user_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> None:
    """Log audit event"""
    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        resource=resource,
        action=action,
        outcome=outcome,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id,
        details=json.dumps(details) if details else None,
        error_message=error_message,
        tenant_id=tenant_id
    )
    
    db.add(audit_log)
    await db.commit()