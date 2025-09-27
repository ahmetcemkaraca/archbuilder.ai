"""
ArchBuilder.AI License and Subscription API Endpoints

This module provides API endpoints for license and subscription management.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.exceptions import (
    LicenseExpiredError,
    LicenseInvalidError,
    SubscriptionInactiveError,
    UsageLimitExceededError,
)
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.license_service import (
    LicenseInfo,
    LicenseService,
    LicenseType,
    SubscriptionInfo,
    UsageStats,
    UsageType,
    license_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class LicenseResponse(BaseModel):
    """Response model for license information"""

    license_id: str
    license_type: LicenseType
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    features: List[str]
    usage_limits: dict
    metadata: dict


class SubscriptionResponse(BaseModel):
    """Response model for subscription information"""

    subscription_id: str
    plan: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    trial_end: Optional[datetime] = None


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""

    usage_type: str
    current_usage: int
    limit: int
    reset_period: str
    reset_date: datetime
    is_over_limit: bool


class LicenseValidationRequest(BaseModel):
    """Request model for license validation"""

    license_key: Optional[str] = None


class UsageTrackingRequest(BaseModel):
    """Request model for usage tracking"""

    usage_type: UsageType
    amount: int = 1
    metadata: Optional[dict] = None


class FeatureAccessRequest(BaseModel):
    """Request model for feature access check"""

    feature: str


@router.get("/license", response_model=LicenseResponse)
async def get_license_info(
    current_user: User = Depends(get_current_user),
) -> LicenseResponse:
    """
    Get license information for the current user

    Returns:
        LicenseResponse: License information
    """
    try:
        license_info = await license_service.get_license_info(current_user.id)

        return LicenseResponse(
            license_id=license_info.license_id,
            license_type=license_info.license_type,
            issued_at=license_info.issued_at,
            expires_at=license_info.expires_at,
            is_active=license_info.is_active,
            features=license_info.features,
            usage_limits=license_info.usage_limits,
            metadata=license_info.metadata,
        )

    except (LicenseInvalidError, LicenseExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get license info for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_info(
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """
    Get subscription information for the current user

    Returns:
        SubscriptionResponse: Subscription information
    """
    try:
        subscription_info = await license_service.get_subscription_info(current_user.id)

        return SubscriptionResponse(
            subscription_id=subscription_info.subscription_id,
            plan=subscription_info.plan.value,
            status=subscription_info.status.value,
            current_period_start=subscription_info.current_period_start,
            current_period_end=subscription_info.current_period_end,
            cancel_at_period_end=subscription_info.cancel_at_period_end,
            trial_end=subscription_info.trial_end,
        )

    except SubscriptionInactiveError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            f"Failed to get subscription info for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/usage", response_model=List[UsageStatsResponse])
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
) -> List[UsageStatsResponse]:
    """
    Get usage statistics for the current user

    Returns:
        List[UsageStatsResponse]: List of usage statistics
    """
    try:
        usage_stats = await license_service.get_usage_stats(current_user.id)

        return [
            UsageStatsResponse(
                usage_type=stat.usage_type.value,
                current_usage=stat.current_usage,
                limit=stat.limit,
                reset_period=stat.reset_period,
                reset_date=stat.reset_date,
                is_over_limit=stat.is_over_limit,
            )
            for stat in usage_stats
        ]

    except Exception as e:
        logger.error(f"Failed to get usage stats for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/license/validate")
async def validate_license(
    request: LicenseValidationRequest, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Validate license for the current user

    Args:
        request: License validation request
        current_user: Current authenticated user

    Returns:
        dict: Validation result
    """
    try:
        license_info = await license_service.validate_license(
            current_user.id, request.license_key
        )

        return {
            "valid": True,
            "license_id": license_info.license_id,
            "license_type": license_info.license_type.value,
            "expires_at": (
                license_info.expires_at.isoformat() if license_info.expires_at else None
            ),
            "features": license_info.features,
        }

    except (LicenseInvalidError, LicenseExpiredError) as e:
        return {"valid": False, "error": str(e), "error_type": type(e).__name__}
    except Exception as e:
        logger.error(f"License validation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/subscription/check")
async def check_subscription(current_user: User = Depends(get_current_user)) -> dict:
    """
    Check subscription status for the current user

    Returns:
        dict: Subscription check result
    """
    try:
        subscription_info = await license_service.check_subscription_status(
            current_user.id
        )

        return {
            "active": True,
            "subscription_id": subscription_info.subscription_id,
            "plan": subscription_info.plan.value,
            "status": subscription_info.status.value,
            "current_period_end": subscription_info.current_period_end.isoformat(),
            "trial_end": (
                subscription_info.trial_end.isoformat()
                if subscription_info.trial_end
                else None
            ),
        }

    except SubscriptionInactiveError as e:
        return {"active": False, "error": str(e), "error_type": type(e).__name__}
    except Exception as e:
        logger.error(f"Subscription check failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/usage/track")
async def track_usage(
    request: UsageTrackingRequest, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Track usage for the current user

    Args:
        request: Usage tracking request
        current_user: Current authenticated user

    Returns:
        dict: Usage tracking result
    """
    try:
        usage_stats = await license_service.track_usage(
            user_id=current_user.id,
            usage_type=request.usage_type,
            amount=request.amount,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "usage_type": usage_stats.usage_type.value,
            "current_usage": usage_stats.current_usage,
            "limit": usage_stats.limit,
            "reset_period": usage_stats.reset_period,
            "reset_date": usage_stats.reset_date.isoformat(),
            "is_over_limit": usage_stats.is_over_limit,
        }

    except UsageLimitExceededError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Usage tracking failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feature/check")
async def check_feature_access(
    request: FeatureAccessRequest, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Check if user has access to a specific feature

    Args:
        request: Feature access request
        current_user: Current authenticated user

    Returns:
        dict: Feature access result
    """
    try:
        has_access = await license_service.check_feature_access(
            current_user.id, request.feature
        )

        return {"feature": request.feature, "has_access": has_access}

    except Exception as e:
        logger.error(
            f"Feature access check failed for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/features")
async def get_available_features(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get available features for the current user

    Returns:
        dict: Available features
    """
    try:
        license_info = await license_service.get_license_info(current_user.id)

        return {
            "features": license_info.features,
            "license_type": license_info.license_type.value,
            "usage_limits": license_info.usage_limits,
        }

    except (LicenseInvalidError, LicenseExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get features for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/limits")
async def get_usage_limits(current_user: User = Depends(get_current_user)) -> dict:
    """
    Get usage limits for the current user

    Returns:
        dict: Usage limits
    """
    try:
        license_info = await license_service.get_license_info(current_user.id)
        usage_stats = await license_service.get_usage_stats(current_user.id)

        return {
            "license_type": license_info.license_type.value,
            "usage_limits": license_info.usage_limits,
            "current_usage": {
                stat.usage_type.value: {
                    "current": stat.current_usage,
                    "limit": stat.limit,
                    "reset_period": stat.reset_period,
                    "reset_date": stat.reset_date.isoformat(),
                    "is_over_limit": stat.is_over_limit,
                }
                for stat in usage_stats
            },
        }

    except (LicenseInvalidError, LicenseExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get usage limits for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/license/refresh")
async def refresh_license(current_user: User = Depends(get_current_user)) -> dict:
    """
    Refresh license information for the current user

    Returns:
        dict: Refresh result
    """
    try:
        # Clear cache for user
        await license_service._clear_user_cache(current_user.id)

        # Get fresh license info
        license_info = await license_service.get_license_info(current_user.id)

        return {
            "success": True,
            "license_id": license_info.license_id,
            "license_type": license_info.license_type.value,
            "expires_at": (
                license_info.expires_at.isoformat() if license_info.expires_at else None
            ),
            "features": license_info.features,
        }

    except (LicenseInvalidError, LicenseExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"License refresh failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/subscription/refresh")
async def refresh_subscription(current_user: User = Depends(get_current_user)) -> dict:
    """
    Refresh subscription information for the current user

    Returns:
        dict: Refresh result
    """
    try:
        # Clear cache for user
        await license_service._clear_user_cache(current_user.id)

        # Get fresh subscription info
        subscription_info = await license_service.get_subscription_info(current_user.id)

        return {
            "success": True,
            "subscription_id": subscription_info.subscription_id,
            "plan": subscription_info.plan.value,
            "status": subscription_info.status.value,
            "current_period_end": subscription_info.current_period_end.isoformat(),
            "trial_end": (
                subscription_info.trial_end.isoformat()
                if subscription_info.trial_end
                else None
            ),
        }

    except SubscriptionInactiveError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            f"Subscription refresh failed for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_license_status(current_user: User = Depends(get_current_user)) -> dict:
    """
    Get comprehensive license and subscription status

    Returns:
        dict: Complete status information
    """
    try:
        # Get license info
        license_info = await license_service.get_license_info(current_user.id)

        # Get subscription info
        subscription_info = await license_service.get_subscription_info(current_user.id)

        # Get usage stats
        usage_stats = await license_service.get_usage_stats(current_user.id)

        return {
            "license": {
                "license_id": license_info.license_id,
                "license_type": license_info.license_type.value,
                "issued_at": license_info.issued_at.isoformat(),
                "expires_at": (
                    license_info.expires_at.isoformat()
                    if license_info.expires_at
                    else None
                ),
                "is_active": license_info.is_active,
                "features": license_info.features,
                "usage_limits": license_info.usage_limits,
            },
            "subscription": {
                "subscription_id": subscription_info.subscription_id,
                "plan": subscription_info.plan.value,
                "status": subscription_info.status.value,
                "current_period_start": subscription_info.current_period_start.isoformat(),
                "current_period_end": subscription_info.current_period_end.isoformat(),
                "cancel_at_period_end": subscription_info.cancel_at_period_end,
                "trial_end": (
                    subscription_info.trial_end.isoformat()
                    if subscription_info.trial_end
                    else None
                ),
            },
            "usage": {
                stat.usage_type.value: {
                    "current": stat.current_usage,
                    "limit": stat.limit,
                    "reset_period": stat.reset_period,
                    "reset_date": stat.reset_date.isoformat(),
                    "is_over_limit": stat.is_over_limit,
                }
                for stat in usage_stats
            },
        }

    except (LicenseInvalidError, LicenseExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except SubscriptionInactiveError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            f"Failed to get license status for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
