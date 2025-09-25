"""
ArchBuilder.AI License and Subscription Middleware

This middleware handles license validation and subscription checks for API requests.
"""

import logging
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    LicenseExpiredError,
    LicenseInvalidError,
    SubscriptionInactiveError,
    UsageLimitExceededError,
)
from app.services.license_service import LicenseService, UsageType

logger = logging.getLogger(__name__)


class LicenseMiddleware(BaseHTTPMiddleware):
    """Middleware for license and subscription validation"""
    
    def __init__(self, app, license_service: LicenseService):
        super().__init__(app)
        self.license_service = license_service
        
        # Define routes that require license validation
        self.license_required_routes = {
            "/v1/ai/generate-layout",
            "/v1/ai/optimize-design",
            "/v1/ai/code-check",
            "/v1/ai/analyze-performance",
            "/v1/projects",
            "/v1/files/process",
            "/v1/collaboration",
        }
        
        # Define routes that require subscription validation
        self.subscription_required_routes = {
            "/v1/ai/generate-layout",
            "/v1/ai/optimize-design",
            "/v1/ai/code-check",
            "/v1/ai/analyze-performance",
            "/v1/collaboration",
        }
        
        # Define usage tracking for different routes
        self.usage_tracking_routes = {
            "/v1/ai/generate-layout": UsageType.AI_DESIGN_GENERATION,
            "/v1/ai/optimize-design": UsageType.AI_OPTIMIZATION,
            "/v1/ai/code-check": UsageType.AI_CODE_CHECK,
            "/v1/files/process": UsageType.FILE_PROCESSING,
            "/v1/collaboration/join": UsageType.COLLABORATION_SESSIONS,
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through license and subscription middleware"""
        try:
            # Skip license checks for health and public endpoints
            if self._should_skip_license_check(request):
                return await call_next(request)
            
            # Extract user ID from request
            user_id = await self._extract_user_id(request)
            if not user_id:
                return JSONResponse(
                    status_code=401,
                    content={"error": "User authentication required"}
                )
            
            # Check license if required
            if self._requires_license_validation(request):
                try:
                    await self.license_service.validate_license(user_id)
                except (LicenseInvalidError, LicenseExpiredError) as e:
                    return JSONResponse(
                        status_code=403,
                        content={"error": f"License validation failed: {str(e)}"}
                    )
            
            # Check subscription if required
            if self._requires_subscription_validation(request):
                try:
                    await self.license_service.check_subscription_status(user_id)
                except SubscriptionInactiveError as e:
                    return JSONResponse(
                        status_code=403,
                        content={"error": f"Subscription validation failed: {str(e)}"}
                    )
            
            # Track usage if required
            if self._requires_usage_tracking(request):
                usage_type = self.usage_tracking_routes.get(request.url.path)
                if usage_type:
                    try:
                        await self.license_service.track_usage(
                            user_id=user_id,
                            usage_type=usage_type,
                            amount=1,
                            metadata={
                                "endpoint": request.url.path,
                                "method": request.method,
                                "timestamp": str(request.state.start_time) if hasattr(request.state, 'start_time') else None
                            }
                        )
                    except UsageLimitExceededError as e:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": f"Usage limit exceeded: {str(e)}",
                                "retry_after": 3600  # 1 hour
                            }
                        )
            
            # Process request
            response = await call_next(request)
            
            # Add license and subscription headers
            await self._add_license_headers(response, user_id)
            
            return response
            
        except Exception as e:
            logger.error(f"License middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def _should_skip_license_check(self, request: Request) -> bool:
        """Check if license validation should be skipped for this request"""
        skip_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/v1/auth/login",
            "/v1/auth/register",
            "/v1/auth/refresh",
            "/v1/public",
        }
        
        return request.url.path in skip_paths
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try to get user ID from various sources
        
        # 1. From Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # This would typically decode the JWT token
            # For now, we'll simulate user ID extraction
            user_id = await self._extract_user_from_token(token)
            if user_id:
                return user_id
        
        # 2. From API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user_id = await self._extract_user_from_api_key(api_key)
            if user_id:
                return user_id
        
        # 3. From session (for web requests)
        session = request.cookies.get("session_id")
        if session:
            user_id = await self._extract_user_from_session(session)
            if user_id:
                return user_id
        
        return None
    
    async def _extract_user_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        try:
            # This would typically decode and validate the JWT token
            # For now, we'll simulate with mock data
            if token == "valid_token_123":
                return "user_123"
            elif token == "valid_token_456":
                return "user_456"
            return None
        except Exception:
            return None
    
    async def _extract_user_from_api_key(self, api_key: str) -> Optional[str]:
        """Extract user ID from API key"""
        try:
            # This would typically validate the API key and get user ID
            # For now, we'll simulate with mock data
            api_key_mapping = {
                "api_key_123": "user_123",
                "api_key_456": "user_456",
                "api_key_789": "user_789"
            }
            return api_key_mapping.get(api_key)
        except Exception:
            return None
    
    async def _extract_user_from_session(self, session_id: str) -> Optional[str]:
        """Extract user ID from session"""
        try:
            # This would typically validate the session and get user ID
            # For now, we'll simulate with mock data
            session_mapping = {
                "session_123": "user_123",
                "session_456": "user_456"
            }
            return session_mapping.get(session_id)
        except Exception:
            return None
    
    def _requires_license_validation(self, request: Request) -> bool:
        """Check if request requires license validation"""
        return any(request.url.path.startswith(route) for route in self.license_required_routes)
    
    def _requires_subscription_validation(self, request: Request) -> bool:
        """Check if request requires subscription validation"""
        return any(request.url.path.startswith(route) for route in self.subscription_required_routes)
    
    def _requires_usage_tracking(self, request: Request) -> bool:
        """Check if request requires usage tracking"""
        return request.url.path in self.usage_tracking_routes
    
    async def _add_license_headers(self, response: Response, user_id: str) -> None:
        """Add license and subscription headers to response"""
        try:
            # Get license info
            license_info = await self.license_service.get_license_info(user_id)
            
            # Get subscription info
            subscription_info = await self.license_service.get_subscription_info(user_id)
            
            # Get usage stats
            usage_stats = await self.license_service.get_usage_stats(user_id)
            
            # Add headers
            response.headers["X-License-Type"] = license_info.license_type.value
            response.headers["X-License-Expires"] = license_info.expires_at.isoformat() if license_info.expires_at else "never"
            response.headers["X-Subscription-Plan"] = subscription_info.plan.value
            response.headers["X-Subscription-Status"] = subscription_info.status.value
            
            # Add usage headers
            for usage_stat in usage_stats:
                header_name = f"X-Usage-{usage_stat.usage_type.value.replace('_', '-').title()}"
                response.headers[header_name] = f"{usage_stat.current_usage}/{usage_stat.limit}"
            
        except Exception as e:
            logger.error(f"Failed to add license headers: {str(e)}")


class LicenseDecorator:
    """Decorator for license validation on specific endpoints"""
    
    def __init__(self, license_service: LicenseService):
        self.license_service = license_service
    
    def require_license(self, license_types: Optional[list] = None):
        """Decorator to require specific license types"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user_id from function arguments or request
                user_id = self._extract_user_id_from_args(args, kwargs)
                if not user_id:
                    raise HTTPException(status_code=401, detail="User authentication required")
                
                # Validate license
                try:
                    license_info = await self.license_service.validate_license(user_id)
                    
                    # Check license type if specified
                    if license_types and license_info.license_type not in license_types:
                        raise HTTPException(
                            status_code=403, 
                            detail=f"License type {license_info.license_type} not allowed. Required: {license_types}"
                        )
                    
                    # Add license info to kwargs
                    kwargs['license_info'] = license_info
                    
                except (LicenseInvalidError, LicenseExpiredError) as e:
                    raise HTTPException(status_code=403, detail=str(e))
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_subscription(self, plans: Optional[list] = None):
        """Decorator to require specific subscription plans"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user_id from function arguments or request
                user_id = self._extract_user_id_from_args(args, kwargs)
                if not user_id:
                    raise HTTPException(status_code=401, detail="User authentication required")
                
                # Validate subscription
                try:
                    subscription_info = await self.license_service.check_subscription_status(user_id)
                    
                    # Check subscription plan if specified
                    if plans and subscription_info.plan not in plans:
                        raise HTTPException(
                            status_code=403, 
                            detail=f"Subscription plan {subscription_info.plan} not allowed. Required: {plans}"
                        )
                    
                    # Add subscription info to kwargs
                    kwargs['subscription_info'] = subscription_info
                    
                except SubscriptionInactiveError as e:
                    raise HTTPException(status_code=403, detail=str(e))
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def track_usage(self, usage_type: UsageType, amount: int = 1):
        """Decorator to track usage for an endpoint"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user_id from function arguments or request
                user_id = self._extract_user_id_from_args(args, kwargs)
                if not user_id:
                    raise HTTPException(status_code=401, detail="User authentication required")
                
                # Track usage
                try:
                    await self.license_service.track_usage(
                        user_id=user_id,
                        usage_type=usage_type,
                        amount=amount,
                        metadata={
                            "endpoint": func.__name__,
                            "timestamp": str(kwargs.get('timestamp', ''))
                        }
                    )
                except UsageLimitExceededError as e:
                    raise HTTPException(status_code=429, detail=str(e))
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _extract_user_id_from_args(self, args, kwargs) -> Optional[str]:
        """Extract user_id from function arguments"""
        # Try to get user_id from various sources
        
        # 1. From kwargs
        if 'user_id' in kwargs:
            return kwargs['user_id']
        
        # 2. From request object
        for arg in args:
            if hasattr(arg, 'user_id'):
                return arg.user_id
            if hasattr(arg, 'headers') and 'X-User-ID' in arg.headers:
                return arg.headers['X-User-ID']
        
        # 3. From kwargs request object
        if 'request' in kwargs:
            request = kwargs['request']
            if hasattr(request, 'user_id'):
                return request.user_id
            if hasattr(request, 'headers') and 'X-User-ID' in request.headers:
                return request.headers['X-User-ID']
        
        return None


# Global license decorator instance
license_decorator = LicenseDecorator(LicenseService())
