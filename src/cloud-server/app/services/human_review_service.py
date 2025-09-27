"""
Human Review Service for ArchBuilder.AI

AI-Human collaboration review system for architectural layouts.
Manages review queue, feedback processing, and quality assurance.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

# Import from current package structure - adjust as needed
try:
    from structlog import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# These imports may need adjustment based on actual package structure
# from ..schemas.layout_schemas import LayoutGenerationRequest, LayoutResult, ValidationResult
# from ..core.exceptions import ValidationError
# from ..utils.notifications import NotificationService

logger = get_logger(__name__)


class ReviewStatus(str, Enum):
    """Review durumu enum"""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_NEEDED = "revision_needed"
    COMPLETED = "completed"


class ReviewPriority(str, Enum):
    """Review öncelik seviyeleri"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewerRole(str, Enum):
    """Reviewer rolleri"""

    ARCHITECT = "architect"
    ENGINEER = "engineer"
    PROJECT_MANAGER = "project_manager"
    CLIENT = "client"
    ADMIN = "admin"


class ReviewFeedback(BaseModel):
    """Review feedback modeli"""

    reviewer_id: str
    reviewer_name: str
    reviewer_role: ReviewerRole
    rating: int = Field(ge=1, le=5, description="1-5 arası rating")
    comments: str = Field(max_length=2000)
    suggestions: List[str] = []
    approval_status: bool
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ReviewItem(BaseModel):
    """Review queue item"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    layout_id: str
    request_data: Any  # LayoutGenerationRequest
    generated_result: Any  # LayoutResult
    validation_results: List[Any]  # List[ValidationResult]
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.MEDIUM
    assigned_reviewer: Optional[str] = None
    feedback_history: List[ReviewFeedback] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    tags: List[str] = []

    # AI analysis results
    ai_confidence_score: Optional[float] = None
    complexity_score: Optional[float] = None
    risk_factors: List[str] = []

    class Config:
        use_enum_values = True


class ReviewStats(BaseModel):
    """Review istatistikleri"""

    total_reviews: int
    pending_reviews: int
    completed_reviews: int
    avg_review_time_hours: float
    approval_rate: float
    reviewer_performance: Dict[str, Any]


class HumanReviewService:
    """
    AI-Human collaboration review service

    Bu servis şu özellikler sağlar:
    - Review queue management
    - AI confidence-based review routing
    - Feedback collection and processing
    - Review performance analytics
    - Quality assurance workflows
    """

    def __init__(self, notification_service: Optional[NotificationService] = None):
        self.notification_service = notification_service
        self.review_queue: Dict[str, ReviewItem] = {}
        self.reviewer_workload: Dict[str, int] = {}

        # Review routing thresholds
        self.auto_approve_threshold = 0.95  # AI confidence for auto-approval
        self.priority_review_threshold = 0.7  # Below this needs priority review
        self.max_reviewer_workload = 10  # Max concurrent reviews per reviewer

    async def submit_for_review(
        self,
        layout_id: str,
        request: Any,  # LayoutGenerationRequest
        result: Any,  # LayoutResult
        validation_results: List[Any],  # List[ValidationResult]
        ai_confidence: Optional[float] = None,
    ) -> str:
        """
        Layout'u human review için queue'ya ekle

        Args:
            layout_id: Layout ID
            request: Original generation request
            result: AI generated result
            validation_results: Validation sonuçları
            ai_confidence: AI güven skoru

        Returns:
            str: Review item ID
        """

        logger.info(
            "Layout review için queue'ya ekleniyor",
            layout_id=layout_id,
            ai_confidence=ai_confidence,
        )

        # Determine priority and auto-routing
        priority, auto_actions = await self._analyze_review_requirements(
            request, result, validation_results, ai_confidence
        )

        # Create review item
        review_item = ReviewItem(
            layout_id=layout_id,
            request_data=request,
            generated_result=result,
            validation_results=validation_results,
            priority=priority,
            ai_confidence_score=ai_confidence,
            complexity_score=await self._calculate_complexity_score(request, result),
            risk_factors=await self._identify_risk_factors(validation_results),
            deadline=self._calculate_deadline(priority),
        )

        # Check for auto-approval
        if auto_actions.get("auto_approve", False):
            review_item.status = ReviewStatus.APPROVED
            review_item.feedback_history.append(
                ReviewFeedback(
                    reviewer_id="ai_system",
                    reviewer_name="AI Auto-Review",
                    reviewer_role=ReviewerRole.ADMIN,
                    rating=5,
                    comments=f"Otomatik onay - AI güven skoru: {ai_confidence:.2f}",
                    suggestions=[],
                    approval_status=True,
                )
            )
            logger.info("Layout otomatik onaylandı", layout_id=layout_id)

        else:
            # Assign to reviewer
            assigned_reviewer = await self._assign_reviewer(review_item)
            if assigned_reviewer:
                review_item.assigned_reviewer = assigned_reviewer
                review_item.status = ReviewStatus.IN_REVIEW

                # Send notification
                if self.notification_service:
                    await self.notification_service.send_review_notification(
                        reviewer_id=assigned_reviewer, review_item=review_item
                    )

        # Add to queue
        self.review_queue[review_item.id] = review_item

        logger.info(
            "Review queue'ya eklendi",
            review_id=review_item.id,
            layout_id=layout_id,
            status=review_item.status,
            priority=review_item.priority,
            assigned_reviewer=review_item.assigned_reviewer,
        )

        return review_item.id

    async def get_review_item(self, review_id: str) -> Optional[ReviewItem]:
        """Review item'ı getir"""
        return self.review_queue.get(review_id)

    async def get_review_queue(
        self,
        reviewer_id: Optional[str] = None,
        status: Optional[ReviewStatus] = None,
        priority: Optional[ReviewPriority] = None,
        limit: int = 50,
    ) -> List[ReviewItem]:
        """
        Review queue'yu filtrele ve getir

        Args:
            reviewer_id: Specific reviewer filter
            status: Status filter
            priority: Priority filter
            limit: Maximum items to return

        Returns:
            List[ReviewItem]: Filtered review items
        """

        items = list(self.review_queue.values())

        # Apply filters
        if reviewer_id:
            items = [item for item in items if item.assigned_reviewer == reviewer_id]

        if status:
            items = [item for item in items if item.status == status]

        if priority:
            items = [item for item in items if item.priority == priority]

        # Sort by priority and creation date
        priority_order = {
            ReviewPriority.CRITICAL: 4,
            ReviewPriority.HIGH: 3,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 1,
        }

        items.sort(
            key=lambda x: (priority_order.get(x.priority, 0), x.created_at),
            reverse=True,
        )

        return items[:limit]

    async def submit_feedback(
        self,
        review_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_role: ReviewerRole,
        rating: int,
        comments: str,
        suggestions: List[str],
        approval_status: bool,
    ) -> bool:
        """
        Review feedback'i submit et

        Args:
            review_id: Review item ID
            reviewer_id: Reviewer ID
            reviewer_name: Reviewer name
            reviewer_role: Reviewer role
            rating: 1-5 rating
            comments: Feedback comments
            suggestions: Improvement suggestions
            approval_status: Approve/reject decision

        Returns:
            bool: Success status
        """

        review_item = self.review_queue.get(review_id)
        if not review_item:
            raise ValidationError(f"Review item not found: {review_id}")

        # Create feedback
        feedback = ReviewFeedback(
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_role=reviewer_role,
            rating=rating,
            comments=comments,
            suggestions=suggestions,
            approval_status=approval_status,
        )

        # Add to feedback history
        review_item.feedback_history.append(feedback)
        review_item.updated_at = datetime.now()

        # Update status based on feedback
        if approval_status:
            review_item.status = ReviewStatus.APPROVED
        else:
            if rating <= 2:
                review_item.status = ReviewStatus.REJECTED
            else:
                review_item.status = ReviewStatus.REVISION_NEEDED

        # Update reviewer workload
        if reviewer_id in self.reviewer_workload:
            self.reviewer_workload[reviewer_id] -= 1

        logger.info(
            "Review feedback alındı",
            review_id=review_id,
            reviewer_id=reviewer_id,
            rating=rating,
            approval_status=approval_status,
            new_status=review_item.status,
        )

        # Send notifications for status changes
        if self.notification_service:
            await self.notification_service.send_review_complete_notification(
                review_item=review_item, feedback=feedback
            )

        return True

    async def get_reviewer_dashboard(self, reviewer_id: str) -> Dict[str, Any]:
        """
        Reviewer dashboard verilerini getir

        Args:
            reviewer_id: Reviewer ID

        Returns:
            Dict: Dashboard data
        """

        # Get reviewer's items
        assigned_items = [
            item
            for item in self.review_queue.values()
            if item.assigned_reviewer == reviewer_id
        ]

        pending_items = [
            item for item in assigned_items if item.status == ReviewStatus.IN_REVIEW
        ]
        completed_items = [
            item
            for item in assigned_items
            if item.status
            in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.COMPLETED]
        ]

        # Calculate performance metrics
        total_reviews = len(completed_items)
        avg_rating = 0
        if completed_items:
            ratings = []
            for item in completed_items:
                if item.feedback_history:
                    ratings.extend(
                        [
                            f.rating
                            for f in item.feedback_history
                            if f.reviewer_id == reviewer_id
                        ]
                    )
            if ratings:
                avg_rating = sum(ratings) / len(ratings)

        # Calculate average review time
        avg_review_time_hours = 0
        if completed_items:
            review_times = []
            for item in completed_items:
                time_diff = item.updated_at - item.created_at
                review_times.append(
                    time_diff.total_seconds() / 3600
                )  # Convert to hours
            if review_times:
                avg_review_time_hours = sum(review_times) / len(review_times)

        dashboard = {
            "reviewer_id": reviewer_id,
            "current_workload": len(pending_items),
            "pending_reviews": pending_items,
            "completed_count": total_reviews,
            "avg_rating_given": round(avg_rating, 2),
            "avg_review_time_hours": round(avg_review_time_hours, 2),
            "priority_breakdown": self._get_priority_breakdown(pending_items),
            "recent_activity": self._get_recent_activity(reviewer_id),
        }

        return dashboard

    async def get_system_stats(self) -> ReviewStats:
        """System review istatistikleri"""

        all_items = list(self.review_queue.values())
        pending_items = [
            item for item in all_items if item.status == ReviewStatus.PENDING
        ]
        completed_items = [
            item
            for item in all_items
            if item.status
            in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.COMPLETED]
        ]

        # Calculate approval rate
        approved_items = [
            item for item in completed_items if item.status == ReviewStatus.APPROVED
        ]
        approval_rate = (
            len(approved_items) / len(completed_items) if completed_items else 0
        )

        # Calculate average review time
        avg_review_time_hours = 0
        if completed_items:
            review_times = []
            for item in completed_items:
                time_diff = item.updated_at - item.created_at
                review_times.append(time_diff.total_seconds() / 3600)
            if review_times:
                avg_review_time_hours = sum(review_times) / len(review_times)

        # Reviewer performance
        reviewer_performance = {}
        for reviewer_id in self.reviewer_workload.keys():
            reviewer_items = [
                item for item in all_items if item.assigned_reviewer == reviewer_id
            ]
            reviewer_performance[reviewer_id] = {
                "total_reviews": len(reviewer_items),
                "current_workload": self.reviewer_workload[reviewer_id],
                "avg_rating": self._calculate_reviewer_avg_rating(
                    reviewer_id, reviewer_items
                ),
            }

        return ReviewStats(
            total_reviews=len(all_items),
            pending_reviews=len(pending_items),
            completed_reviews=len(completed_items),
            avg_review_time_hours=round(avg_review_time_hours, 2),
            approval_rate=round(approval_rate * 100, 2),
            reviewer_performance=reviewer_performance,
        )

    async def _analyze_review_requirements(
        self,
        request: Any,  # LayoutGenerationRequest
        result: Any,  # LayoutResult - unused in current impl
        validation_results: List[Any],  # List[ValidationResult]
        ai_confidence: Optional[float],
    ) -> tuple[ReviewPriority, Dict[str, Any]]:
        """Review requirements analizi"""

        auto_actions = {"auto_approve": False}

        # Auto-approval check
        has_errors = any(len(vr.errors) > 0 for vr in validation_results)
        if (
            ai_confidence
            and ai_confidence >= self.auto_approve_threshold
            and not has_errors
            and all(vr.status.value == "valid" for vr in validation_results)
        ):
            auto_actions["auto_approve"] = True
            return ReviewPriority.LOW, auto_actions

        # Priority calculation based on multiple factors
        priority_score = 0

        # AI confidence factor
        if ai_confidence:
            if ai_confidence < self.priority_review_threshold:
                priority_score += 2
            elif ai_confidence < 0.85:
                priority_score += 1

        # Validation errors factor
        error_count = sum(len(vr.errors) for vr in validation_results)
        warning_count = sum(len(vr.warnings) for vr in validation_results)

        priority_score += error_count * 2 + warning_count

        # Project size factor (use rooms from requirements if available)
        room_count = len(getattr(request, 'rooms', []))
        if room_count > 10:
            priority_score += 2
        elif room_count > 5:
            priority_score += 1

        # Budget factor (if high budget, higher priority)
        budget = getattr(request, 'budget', None)
        if budget and budget > 1000000:
            priority_score += 1

        # Determine priority
        if priority_score >= 5:
            priority = ReviewPriority.CRITICAL
        elif priority_score >= 3:
            priority = ReviewPriority.HIGH
        elif priority_score >= 1:
            priority = ReviewPriority.MEDIUM
        else:
            priority = ReviewPriority.LOW

        return priority, auto_actions

    async def _assign_reviewer(self, review_item: ReviewItem) -> Optional[str]:
        """En uygun reviewer'ı assign et"""

        # Get available reviewers (mock implementation)
        available_reviewers = [
            "reviewer_001",  # Senior Architect
            "reviewer_002",  # Structural Engineer
            "reviewer_003",  # Project Manager
        ]

        # Find reviewer with lowest workload
        best_reviewer = None
        min_workload = float('inf')

        for reviewer_id in available_reviewers:
            current_workload = self.reviewer_workload.get(reviewer_id, 0)

            if (
                current_workload < min_workload
                and current_workload < self.max_reviewer_workload
            ):
                min_workload = current_workload
                best_reviewer = reviewer_id

        if best_reviewer:
            self.reviewer_workload[best_reviewer] = (
                self.reviewer_workload.get(best_reviewer, 0) + 1
            )

        return best_reviewer

    async def _calculate_complexity_score(
        self, request: Any, result: Any  # LayoutGenerationRequest  # LayoutResult
    ) -> float:
        """Layout complexity score hesapla"""

        score = 0.0

        # Room count factor (use rooms from request if available)
        room_count = len(getattr(request, 'rooms', []))
        score += min(room_count * 0.1, 1.0)  # Max 1.0 for rooms

        # Element count factor from layout_data if available
        if result.layout_data:
            layout_data = result.layout_data
            total_elements = (
                len(getattr(layout_data, 'walls', []))
                + len(getattr(layout_data, 'doors', []))
                + len(getattr(layout_data, 'windows', []))
            )
            score += min(total_elements * 0.02, 1.0)  # Max 1.0 for elements

        # Special requirements factor (check for special_requirements attribute)
        special_reqs = getattr(request, 'special_requirements', [])
        special_requirements = sum(
            1
            for req in special_reqs
            if req
            in ["accessible_design", "fire_safety", "seismic", "energy_efficient"]
        )
        score += special_requirements * 0.2

        return min(score, 5.0)  # Max score 5.0

    async def _identify_risk_factors(self, validation_results: List[Any]) -> List[str]:
        """Risk factors identification"""

        risk_factors = []

        for result in validation_results:
            # Check errors for risk factors
            for error in result.errors:
                error_msg = error.message.lower()
                if "accessibility" in error_msg or "engelli" in error_msg:
                    risk_factors.append("accessibility_compliance")
                if "fire" in error_msg or "yangın" in error_msg:
                    risk_factors.append("fire_safety")
                if "structural" in error_msg or "yapısal" in error_msg:
                    risk_factors.append("structural_integrity")
                if "building_code" in error_msg or "yapı_yönetmelik" in error_msg:
                    risk_factors.append("building_code_violation")

        return list(set(risk_factors))  # Remove duplicates

    def _calculate_deadline(self, priority: ReviewPriority) -> datetime:
        """Review deadline hesapla"""

        now = datetime.now()

        if priority == ReviewPriority.CRITICAL:
            return now + timedelta(hours=4)
        elif priority == ReviewPriority.HIGH:
            return now + timedelta(hours=24)
        elif priority == ReviewPriority.MEDIUM:
            return now + timedelta(days=3)
        else:  # LOW
            return now + timedelta(days=7)

    def _get_priority_breakdown(self, items: List[ReviewItem]) -> Dict[str, int]:
        """Priority breakdown statistics"""

        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for item in items:
            breakdown[item.priority.value] += 1

        return breakdown

    def _get_recent_activity(
        self, reviewer_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recent reviewer activity"""

        activities = []

        # Get reviewer's recent reviews
        reviewer_items = [
            item
            for item in self.review_queue.values()
            if item.assigned_reviewer == reviewer_id
        ]

        # Sort by updated_at
        reviewer_items.sort(key=lambda x: x.updated_at, reverse=True)

        for item in reviewer_items[:limit]:
            latest_feedback = None
            if item.feedback_history:
                reviewer_feedbacks = [
                    f for f in item.feedback_history if f.reviewer_id == reviewer_id
                ]
                if reviewer_feedbacks:
                    latest_feedback = max(
                        reviewer_feedbacks, key=lambda x: x.created_at
                    )

            activities.append(
                {
                    "layout_id": item.layout_id,
                    "status": item.status.value,
                    "updated_at": item.updated_at.isoformat(),
                    "rating": latest_feedback.rating if latest_feedback else None,
                    "approval_status": (
                        latest_feedback.approval_status if latest_feedback else None
                    ),
                }
            )

        return activities

    def _calculate_reviewer_avg_rating(
        self, reviewer_id: str, items: List[ReviewItem]
    ) -> float:
        """Reviewer average rating hesapla"""

        ratings = []

        for item in items:
            reviewer_feedbacks = [
                f for f in item.feedback_history if f.reviewer_id == reviewer_id
            ]
            ratings.extend([f.rating for f in reviewer_feedbacks])

        return sum(ratings) / len(ratings) if ratings else 0.0

    async def cleanup_old_reviews(self, days: int = 30) -> int:
        """Eski review'ları temizle"""

        cutoff_date = datetime.now() - timedelta(days=days)

        items_to_remove = [
            item_id
            for item_id, item in self.review_queue.items()
            if item.status
            in [ReviewStatus.APPROVED, ReviewStatus.COMPLETED, ReviewStatus.REJECTED]
            and item.updated_at < cutoff_date
        ]

        for item_id in items_to_remove:
            del self.review_queue[item_id]

        logger.info(f"Cleaned up {len(items_to_remove)} old review items")

        return len(items_to_remove)
