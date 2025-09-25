"""
ArchBuilder.AI License and Subscription Management Service

This service handles license validation, subscription management, and usage tracking
for ArchBuilder.AI cloud services.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import redis
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import (
    LicenseExpiredError,
    LicenseInvalidError,
    SubscriptionInactiveError,
    UsageLimitExceededError,
)
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus

logger = logging.getLogger(__name__)


class LicenseType(str, Enum):
    """License types for ArchBuilder.AI"""
    TRIAL = "trial"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    EDUCATIONAL = "educational"
    NON_PROFIT = "non_profit"


class UsageType(str, Enum):
    """Types of usage that can be tracked"""
    AI_DESIGN_GENERATION = "ai_design_generation"
    AI_OPTIMIZATION = "ai_optimization"
    AI_CODE_CHECK = "ai_code_check"
    FILE_PROCESSING = "file_processing"
    API_REQUESTS = "api_requests"
    STORAGE_GB = "storage_gb"
    COLLABORATION_SESSIONS = "collaboration_sessions"


class LicenseInfo(BaseModel):
    """License information model"""
    license_id: str
    user_id: str
    license_type: LicenseType
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    features: List[str] = Field(default_factory=list)
    usage_limits: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)


class UsageStats(BaseModel):
    """Usage statistics model"""
    usage_type: UsageType
    current_usage: int
    limit: int
    reset_period: str  # daily, monthly, yearly
    reset_date: datetime
    is_over_limit: bool = False


class SubscriptionInfo(BaseModel):
    """Subscription information model"""
    subscription_id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None
    usage_stats: List[UsageStats] = Field(default_factory=list)


class LicenseService:
    """Service for managing licenses and subscriptions"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.license_cache_ttl = 300  # 5 minutes
        self.usage_cache_ttl = 60  # 1 minute
    
    async def validate_license(self, user_id: str, license_key: Optional[str] = None) -> LicenseInfo:
        """
        Validate user license and return license information
        
        Args:
            user_id: User ID to validate license for
            license_key: Optional license key for validation
            
        Returns:
            LicenseInfo: License information
            
        Raises:
            LicenseInvalidError: If license is invalid
            LicenseExpiredError: If license has expired
        """
        try:
            # Check cache first
            cache_key = f"license:{user_id}"
            cached_license = await self._get_cached_license(cache_key)
            if cached_license:
                return cached_license
            
            # Get license from database
            license_info = await self._get_license_from_db(user_id, license_key)
            
            # Validate license
            await self._validate_license_info(license_info)
            
            # Cache license info
            await self._cache_license(cache_key, license_info)
            
            return license_info
            
        except Exception as e:
            logger.error(f"License validation failed for user {user_id}: {str(e)}")
            raise LicenseInvalidError(f"License validation failed: {str(e)}")
    
    async def check_subscription_status(self, user_id: str) -> SubscriptionInfo:
        """
        Check user subscription status and return subscription information
        
        Args:
            user_id: User ID to check subscription for
            
        Returns:
            SubscriptionInfo: Subscription information
            
        Raises:
            SubscriptionInactiveError: If subscription is inactive
        """
        try:
            # Check cache first
            cache_key = f"subscription:{user_id}"
            cached_subscription = await self._get_cached_subscription(cache_key)
            if cached_subscription:
                return cached_subscription
            
            # Get subscription from database
            subscription_info = await self._get_subscription_from_db(user_id)
            
            # Validate subscription
            await self._validate_subscription_info(subscription_info)
            
            # Cache subscription info
            await self._cache_subscription(cache_key, subscription_info)
            
            return subscription_info
            
        except Exception as e:
            logger.error(f"Subscription check failed for user {user_id}: {str(e)}")
            raise SubscriptionInactiveError(f"Subscription check failed: {str(e)}")
    
    async def track_usage(
        self, 
        user_id: str, 
        usage_type: UsageType, 
        amount: int = 1,
        metadata: Optional[Dict] = None
    ) -> UsageStats:
        """
        Track usage for a specific user and usage type
        
        Args:
            user_id: User ID to track usage for
            usage_type: Type of usage to track
            amount: Amount of usage to add
            metadata: Optional metadata for usage tracking
            
        Returns:
            UsageStats: Current usage statistics
            
        Raises:
            UsageLimitExceededError: If usage limit is exceeded
        """
        try:
            # Get current usage
            usage_key = f"usage:{user_id}:{usage_type.value}"
            current_usage = await self._get_current_usage(usage_key)
            
            # Get usage limits
            limits = await self._get_usage_limits(user_id, usage_type)
            
            # Check if adding usage would exceed limits
            new_usage = current_usage + amount
            if new_usage > limits['limit']:
                raise UsageLimitExceededError(
                    f"Usage limit exceeded for {usage_type.value}. "
                    f"Current: {current_usage}, Limit: {limits['limit']}"
                )
            
            # Update usage
            await self._update_usage(usage_key, new_usage, limits['reset_period'])
            
            # Log usage
            await self._log_usage(user_id, usage_type, amount, metadata)
            
            # Return usage stats
            return UsageStats(
                usage_type=usage_type,
                current_usage=new_usage,
                limit=limits['limit'],
                reset_period=limits['reset_period'],
                reset_date=limits['reset_date'],
                is_over_limit=False
            )
            
        except UsageLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Usage tracking failed for user {user_id}: {str(e)}")
            raise
    
    async def get_usage_stats(self, user_id: str) -> List[UsageStats]:
        """
        Get current usage statistics for a user
        
        Args:
            user_id: User ID to get usage stats for
            
        Returns:
            List[UsageStats]: List of usage statistics
        """
        try:
            usage_stats = []
            
            # Get all usage types
            for usage_type in UsageType:
                usage_key = f"usage:{user_id}:{usage_type.value}"
                current_usage = await self._get_current_usage(usage_key)
                limits = await self._get_usage_limits(user_id, usage_type)
                
                usage_stats.append(UsageStats(
                    usage_type=usage_type,
                    current_usage=current_usage,
                    limit=limits['limit'],
                    reset_period=limits['reset_period'],
                    reset_date=limits['reset_date'],
                    is_over_limit=current_usage >= limits['limit']
                ))
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {str(e)}")
            return []
    
    async def check_feature_access(self, user_id: str, feature: str) -> bool:
        """
        Check if user has access to a specific feature
        
        Args:
            user_id: User ID to check feature access for
            feature: Feature name to check access for
            
        Returns:
            bool: True if user has access to feature
        """
        try:
            # Get license info
            license_info = await self.validate_license(user_id)
            
            # Check if feature is in license features
            return feature in license_info.features
            
        except (LicenseInvalidError, LicenseExpiredError):
            return False
        except Exception as e:
            logger.error(f"Feature access check failed for user {user_id}: {str(e)}")
            return False
    
    async def get_license_info(self, user_id: str) -> LicenseInfo:
        """
        Get license information for a user
        
        Args:
            user_id: User ID to get license info for
            
        Returns:
            LicenseInfo: License information
        """
        return await self.validate_license(user_id)
    
    async def get_subscription_info(self, user_id: str) -> SubscriptionInfo:
        """
        Get subscription information for a user
        
        Args:
            user_id: User ID to get subscription info for
            
        Returns:
            SubscriptionInfo: Subscription information
        """
        return await self.check_subscription_status(user_id)
    
    async def _get_license_from_db(self, user_id: str, license_key: Optional[str] = None) -> LicenseInfo:
        """Get license information from database"""
        # This would typically query a database
        # For now, we'll simulate with mock data
        
        # Mock license data based on user_id
        mock_licenses = {
            "user_123": LicenseInfo(
                license_id="lic_123456789",
                user_id=user_id,
                license_type=LicenseType.PROFESSIONAL,
                issued_at=datetime.now() - timedelta(days=30),
                expires_at=datetime.now() + timedelta(days=335),
                is_active=True,
                features=["ai_design", "ai_optimization", "collaboration", "api_access"],
                usage_limits={
                    "ai_design_generation": 1000,
                    "ai_optimization": 500,
                    "api_requests": 10000,
                    "storage_gb": 100
                }
            ),
            "user_456": LicenseInfo(
                license_id="lic_456789012",
                user_id=user_id,
                license_type=LicenseType.ENTERPRISE,
                issued_at=datetime.now() - timedelta(days=60),
                expires_at=None,  # No expiration for enterprise
                is_active=True,
                features=["ai_design", "ai_optimization", "collaboration", "api_access", "advanced_analytics"],
                usage_limits={
                    "ai_design_generation": 10000,
                    "ai_optimization": 5000,
                    "api_requests": 100000,
                    "storage_gb": 1000
                }
            )
        }
        
        return mock_licenses.get(user_id, LicenseInfo(
            license_id="lic_default",
            user_id=user_id,
            license_type=LicenseType.TRIAL,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=14),
            is_active=True,
            features=["ai_design"],
            usage_limits={
                "ai_design_generation": 10,
                "api_requests": 100,
                "storage_gb": 1
            }
        ))
    
    async def _get_subscription_from_db(self, user_id: str) -> SubscriptionInfo:
        """Get subscription information from database"""
        # This would typically query a database
        # For now, we'll simulate with mock data
        
        # Mock subscription data based on user_id
        mock_subscriptions = {
            "user_123": SubscriptionInfo(
                subscription_id="sub_123456789",
                user_id=user_id,
                plan=SubscriptionPlan.PROFESSIONAL,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.now() - timedelta(days=30),
                current_period_end=datetime.now() + timedelta(days=335),
                cancel_at_period_end=False
            ),
            "user_456": SubscriptionInfo(
                subscription_id="sub_456789012",
                user_id=user_id,
                plan=SubscriptionPlan.ENTERPRISE,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.now() - timedelta(days=60),
                current_period_end=datetime.now() + timedelta(days=305),
                cancel_at_period_end=False
            )
        }
        
        return mock_subscriptions.get(user_id, SubscriptionInfo(
            subscription_id="sub_default",
            user_id=user_id,
            plan=SubscriptionPlan.TRIAL,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=14),
            trial_end=datetime.now() + timedelta(days=14)
        ))
    
    async def _validate_license_info(self, license_info: LicenseInfo) -> None:
        """Validate license information"""
        if not license_info.is_active:
            raise LicenseInvalidError("License is not active")
        
        if license_info.expires_at and license_info.expires_at < datetime.now():
            raise LicenseExpiredError("License has expired")
    
    async def _validate_subscription_info(self, subscription_info: SubscriptionInfo) -> None:
        """Validate subscription information"""
        if subscription_info.status != SubscriptionStatus.ACTIVE:
            raise SubscriptionInactiveError("Subscription is not active")
        
        if subscription_info.current_period_end < datetime.now():
            raise SubscriptionInactiveError("Subscription period has ended")
    
    async def _get_usage_limits(self, user_id: str, usage_type: UsageType) -> Dict:
        """Get usage limits for a user and usage type"""
        license_info = await self.validate_license(user_id)
        
        # Get limit from license
        limit = license_info.usage_limits.get(usage_type.value, 0)
        
        # Determine reset period based on usage type
        reset_periods = {
            UsageType.AI_DESIGN_GENERATION: "monthly",
            UsageType.AI_OPTIMIZATION: "monthly",
            UsageType.AI_CODE_CHECK: "monthly",
            UsageType.FILE_PROCESSING: "monthly",
            UsageType.API_REQUESTS: "monthly",
            UsageType.STORAGE_GB: "monthly",
            UsageType.COLLABORATION_SESSIONS: "monthly"
        }
        
        reset_period = reset_periods.get(usage_type, "monthly")
        
        # Calculate reset date
        now = datetime.now()
        if reset_period == "daily":
            reset_date = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif reset_period == "monthly":
            reset_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
            reset_date = reset_date.replace(day=1)
        elif reset_period == "yearly":
            reset_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=365)
        else:
            reset_date = now + timedelta(days=30)
        
        return {
            "limit": limit,
            "reset_period": reset_period,
            "reset_date": reset_date
        }
    
    async def _get_current_usage(self, usage_key: str) -> int:
        """Get current usage from cache"""
        try:
            usage_data = self.redis_client.get(usage_key)
            if usage_data:
                return int(usage_data)
            return 0
        except Exception:
            return 0
    
    async def _update_usage(self, usage_key: str, usage: int, reset_period: str) -> None:
        """Update usage in cache"""
        try:
            # Set usage with appropriate TTL
            ttl = self._get_usage_ttl(reset_period)
            self.redis_client.setex(usage_key, ttl, str(usage))
        except Exception as e:
            logger.error(f"Failed to update usage for key {usage_key}: {str(e)}")
    
    async def _get_usage_ttl(self, reset_period: str) -> int:
        """Get TTL for usage cache based on reset period"""
        ttl_map = {
            "daily": 86400,  # 24 hours
            "monthly": 2592000,  # 30 days
            "yearly": 31536000  # 365 days
        }
        return ttl_map.get(reset_period, 86400)
    
    async def _log_usage(
        self, 
        user_id: str, 
        usage_type: UsageType, 
        amount: int, 
        metadata: Optional[Dict] = None
    ) -> None:
        """Log usage for analytics and billing"""
        try:
            usage_log = {
                "user_id": user_id,
                "usage_type": usage_type.value,
                "amount": amount,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in Redis for real-time analytics
            log_key = f"usage_log:{user_id}:{int(time.time())}"
            self.redis_client.setex(log_key, 86400, json.dumps(usage_log))
            
            # This would typically also store in a database for long-term analytics
            logger.info(f"Usage logged: {usage_log}")
            
        except Exception as e:
            logger.error(f"Failed to log usage: {str(e)}")
    
    async def _get_cached_license(self, cache_key: str) -> Optional[LicenseInfo]:
        """Get cached license information"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                license_dict = json.loads(cached_data)
                return LicenseInfo(**license_dict)
            return None
        except Exception:
            return None
    
    async def _cache_license(self, cache_key: str, license_info: LicenseInfo) -> None:
        """Cache license information"""
        try:
            license_dict = license_info.dict()
            self.redis_client.setex(cache_key, self.license_cache_ttl, json.dumps(license_dict))
        except Exception as e:
            logger.error(f"Failed to cache license: {str(e)}")
    
    async def _get_cached_subscription(self, cache_key: str) -> Optional[SubscriptionInfo]:
        """Get cached subscription information"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                subscription_dict = json.loads(cached_data)
                return SubscriptionInfo(**subscription_dict)
            return None
        except Exception:
            return None
    
    async def _cache_subscription(self, cache_key: str, subscription_info: SubscriptionInfo) -> None:
        """Cache subscription information"""
        try:
            subscription_dict = subscription_info.dict()
            self.redis_client.setex(cache_key, self.license_cache_ttl, json.dumps(subscription_dict))
        except Exception as e:
            logger.error(f"Failed to cache subscription: {str(e)}")


# Global license service instance
license_service = LicenseService()
