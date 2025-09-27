"""
Multi-tenant security middleware for ArchBuilder.AI.
Provides tenant isolation, cross-tenant data access prevention, and audit logging.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


def envelope(success: bool, data: Any = None, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Simple envelope function for responses"""
    return {"success": success, "data": data, "error": error}


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce tenant isolation and prevent cross-tenant data access.
    """
    
    # Paths that don't require tenant isolation
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/v1/auth/login",
        "/v1/auth/register",
        "/v1/auth/refresh"
    }
    
    # Admin-only paths that can access cross-tenant data
    ADMIN_PATHS = {
        "/v1/admin/",
        "/v1/system/"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tenant isolation for excluded paths
        if self._should_skip_path(request.url.path):
            return await call_next(request)
        
        # Add correlation ID for request tracking
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Extract user and tenant information from request
        user_info = await self._extract_user_info(request)
        
        if user_info:
            request.state.user_id = user_info["user_id"]
            request.state.tenant_id = user_info["tenant_id"]
            request.state.user_role = user_info["role"]
            
            # Check admin access for admin paths
            if self._is_admin_path(request.url.path):
                if user_info["role"] != "admin":
                    # Log unauthorized admin access attempt
                    await self._log_security_event(
                        request,
                        "unauthorized_admin_access",
                        "access_denied",
                        user_info["user_id"],
                        error_message="Non-admin user attempted to access admin endpoint"
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content=envelope(False, None, {
                            "message": "Admin access required",
                            "correlation_id": correlation_id
                        })
                    )
        else:
            # No user info available - might be public endpoint
            request.state.user_id = None
            request.state.tenant_id = None
            request.state.user_role = None
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except HTTPException as e:
            # Log HTTP exceptions
            await self._log_security_event(
                request,
                "http_exception",
                "error",
                getattr(request.state, "user_id", None),
                error_message=f"HTTP {e.status_code}: {e.detail}"
            )
            raise
        
        except Exception as e:
            # Log unexpected exceptions
            await self._log_security_event(
                request,
                "unexpected_exception",
                "error",
                getattr(request.state, "user_id", None),
                error_message=str(e)
            )
            raise
    
    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be excluded from tenant isolation"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)
    
    def _is_admin_path(self, path: str) -> bool:
        """Check if path requires admin access"""
        return any(path.startswith(admin_path) for admin_path in self.ADMIN_PATHS)
    
    async def _extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token or API key"""
        
        # Try JWT token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # For now, return basic mock data for any Bearer token
                # Implement proper JWT decoding with TokenManager later
                return {
                    "user_id": f"token_user_{token[:8]}",
                    "tenant_id": None,
                    "role": "user",
                    "session_id": None
                }
            except Exception:
                pass  # Invalid token, try API key
        
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # TODO: Implement proper API key validation with database lookup
            return {
                "user_id": "api_key_user",
                "tenant_id": None,
                "role": "user",
                "session_id": None
            }
        
        return None
    
    async def _log_security_event(
        self,
        request: Request,
        event_type: str,
        outcome: str,
        user_id: Optional[str],
        error_message: Optional[str] = None
    ) -> None:
        """Log security-related events (simplified version)"""
        try:
            # For now, just print to console
            # Later integrate with proper audit logging system
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "unknown")
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            
            print(f"AUDIT: {event_type} | {outcome} | User: {user_id} | IP: {client_ip} | UA: {user_agent} | Path: {request.url.path} | ID: {correlation_id}")
            if error_message:
                print(f"ERROR: {error_message}")
                
        except Exception:
            # Don't let logging failures break the request
            pass
    
    def _get_client_ip(self, request: Request) -> str:
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


class TenantDataFilter:
    """
    Utility class to add tenant filtering to database queries.
    Use this in your service layers to ensure data isolation.
    """
    
    @staticmethod
    def add_tenant_filter(query, model_class, tenant_id: Optional[str]):
        """
        Add tenant filtering to SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            model_class: The model class being queried
            tenant_id: Current user's tenant ID
            
        Returns:
            Modified query with tenant filtering
        """
        # If model has tenant_id field, filter by it
        if hasattr(model_class, 'tenant_id'):
            if tenant_id:
                query = query.where(model_class.tenant_id == tenant_id)
            else:
                # If no tenant_id, only show records without tenant_id (global data)
                query = query.where(model_class.tenant_id.is_(None))
        
        return query
    
    @staticmethod
    def ensure_tenant_access(record, user_tenant_id: Optional[str], user_role: str) -> bool:
        """
        Check if user can access a specific record based on tenant isolation.
        
        Args:
            record: Database record to check
            user_tenant_id: Current user's tenant ID
            user_role: Current user's role
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Admins can access all data
        if user_role == "admin":
            return True
        
        # If record doesn't have tenant_id, it's global data (accessible to all)
        if not hasattr(record, 'tenant_id') or record.tenant_id is None:
            return True
        
        # Record has tenant_id, check if it matches user's tenant
        return record.tenant_id == user_tenant_id
    
    @staticmethod
    def set_tenant_on_create(data_dict: Dict[str, Any], user_tenant_id: Optional[str]) -> Dict[str, Any]:
        """
        Set tenant_id on data being created.
        
        Args:
            data_dict: Data dictionary for creation
            user_tenant_id: Current user's tenant ID
            
        Returns:
            Modified data dictionary with tenant_id set
        """
        if user_tenant_id:
            data_dict["tenant_id"] = user_tenant_id
        
        return data_dict


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware based on user/API key.
    """
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        
        # Default rate limits (requests per hour)
        self.default_limits = {
            "admin": 10000,
            "enterprise_user": 5000,
            "premium_user": 1000,
            "user": 100,
            "anonymous": 20
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc"]:
            return await call_next(request)
        
        # Get user info from request state (set by TenantIsolationMiddleware)
        user_id = getattr(request.state, "user_id", None)
        user_role = getattr(request.state, "user_role", "anonymous")
        
        # Check rate limit
        if await self._is_rate_limited(user_id, user_role, request):
            correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=envelope(False, None, {
                    "message": "Rate limit exceeded",
                    "correlation_id": correlation_id
                })
            )
        
        return await call_next(request)
    
    async def _is_rate_limited(self, user_id: Optional[str], user_role: str, request: Request) -> bool:
        """Check if request should be rate limited"""
        
        # If no Redis client, skip rate limiting
        if not self.redis_client:
            return False
        
        # Determine rate limit
        limit = self.default_limits.get(user_role, self.default_limits["anonymous"])
        
        # Create rate limit key
        if user_id:
            rate_key = f"rate_limit:user:{user_id}"
        else:
            # Use IP for anonymous users
            client_ip = self._get_client_ip(request)
            rate_key = f"rate_limit:ip:{client_ip}"
        
        try:
            # Get current count
            current = await self.redis_client.get(rate_key)
            current = int(current) if current else 0
            
            # Check limit
            if current >= limit:
                return True
            
            # Increment counter with 1 hour expiry
            await self.redis_client.setex(rate_key, 3600, current + 1)
            
            return False
            
        except Exception:
            # If Redis fails, allow the request (fail open)
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"


# Helper functions for use in route handlers
def require_tenant_access(record, request: Request) -> None:
    """
    Verify that current user can access the given record based on tenant isolation.
    Raises HTTPException if access is denied.
    """
    user_tenant_id = getattr(request.state, "tenant_id", None)
    user_role = getattr(request.state, "user_role", "user")
    
    if not TenantDataFilter.ensure_tenant_access(record, user_tenant_id, user_role):
        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Access denied: insufficient tenant permissions",
                "correlation_id": correlation_id
            }
        )


def add_tenant_context(data: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """
    Add tenant context to data being created.
    """
    user_tenant_id = getattr(request.state, "tenant_id", None)
    return TenantDataFilter.set_tenant_on_create(data, user_tenant_id)


# Example usage in route handlers - see documentation for implementation details