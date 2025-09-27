"""
Authentication related database models for ArchBuilder.AI production system.
Includes User, ApiKey, RefreshToken, UserSession, and AuditLog models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(PyEnum):
    """User roles for RBAC system"""
    ADMIN = "admin"
    USER = "user" 
    PREMIUM_USER = "premium_user"
    ENTERPRISE_USER = "enterprise_user"
    READONLY = "readonly"


class ApiKeyStatus(PyEnum):
    """API Key status enum"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SessionStatus(PyEnum):
    """User session status enum"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class User(Base):
    """Enhanced User model for production authentication"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    
    # Enhanced fields for production
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Multi-tenant support
    tenant_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    organization_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    
    # Authentication tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    lockout_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_locked_out(self) -> bool:
        """Check if user is currently locked out"""
        return (self.is_locked and 
                self.lockout_until is not None and 
                self.lockout_until > datetime.utcnow())
    
    def can_login(self) -> bool:
        """Check if user can login"""
        return (self.is_active and 
                self.is_verified and 
                not self.is_locked_out)


class ApiKey(Base):
    """API Key model for secure API access"""
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash: Mapped[str] = mapped_column(String(256), unique=True, index=True)  # Hashed API key
    key_prefix: Mapped[str] = mapped_column(String(16), index=True)  # First 8 chars for identification
    name: Mapped[str] = mapped_column(String(128))  # Human-readable name
    
    # User relationship
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="api_keys")
    
    # Key properties
    status: Mapped[ApiKeyStatus] = mapped_column(Enum(ApiKeyStatus), default=ApiKeyStatus.ACTIVE, index=True)
    permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of permissions
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Rate limiting
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Security
    allowed_ips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of IP addresses
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, status={self.status.value})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        return (self.expires_at is not None and 
                self.expires_at < datetime.utcnow())
    
    @property
    def is_active(self) -> bool:
        """Check if API key is active and usable"""
        return (self.status == ApiKeyStatus.ACTIVE and 
                not self.is_expired)


class RefreshToken(Base):
    """Refresh token model for JWT token renewal"""
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_hash: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    
    # User relationship
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="refresh_tokens")
    
    # Session relationship
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("user_sessions.id"), nullable=True)
    session = relationship("UserSession", back_populates="refresh_tokens")
    
    # Token properties
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Security tracking
    issued_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if refresh token is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if refresh token is valid for use"""
        return not self.is_revoked and not self.is_expired


class UserSession(Base):
    """User session model for session management"""
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User relationship
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="sessions")
    
    # Session properties
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.ACTIVE, index=True)
    device_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON device information
    
    # Security tracking
    ip_address: Mapped[str] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Geo location
    
    # Session timing
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if session is active and valid"""
        return (self.status == SessionStatus.ACTIVE and 
                not self.is_expired)
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()


class AuditLog(Base):
    """Audit log model for security tracking"""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User relationship (optional for system events)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", back_populates="audit_logs")
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(128), index=True)  # login, logout, api_key_created, etc.
    resource: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Resource affected
    action: Mapped[str] = mapped_column(String(128))  # create, read, update, delete, access
    outcome: Mapped[str] = mapped_column(String(32), index=True)  # success, failure, error
    
    # Request details
    ip_address: Mapped[str] = mapped_column(String(45), index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Additional data
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON additional information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-tenant support
    tenant_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, outcome={self.outcome})>"