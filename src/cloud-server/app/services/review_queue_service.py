from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum

from app.database.session import AsyncSession
from app.database.models.review_item import ReviewItem

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """TR: Review durumları"""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewPriority(Enum):
    """TR: Review öncelikleri"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewQueueService:
    """TR: Review queue wiring servisi - P20-T3, P32-T1, P32-T2, P32-T3"""

    def __init__(self):
        self._review_assignments: Dict[str, str] = {}  # TR: item_id -> reviewer_id

    async def create_review_item(
        self,
        db: AsyncSession,
        item_type: str,
        item_data: Dict[str, Any],
        priority: str = "medium",
        assigned_to: Optional[str] = None,
        project_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """TR: Review item oluştur"""
        try:
            review_item = ReviewItem(
                id=str(uuid4()),
                item_type=item_type,
                item_data=item_data,
                status=ReviewStatus.PENDING.value,
                priority=priority,
                assigned_to=assigned_to,
                project_id=project_id,
                created_by=created_by,
            )

            db.add(review_item)
            await db.flush()

            logger.info(f"TR: Review item oluşturuldu: {review_item.id}")

            return {
                "success": True,
                "data": {
                    "id": review_item.id,
                    "status": review_item.status,
                    "priority": review_item.priority,
                    "created_at": review_item.created_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"TR: Review item oluşturma hatası: {e}")
            return {
                "success": False,
                "error": f"TR: Review item oluşturma hatası: {str(e)}",
            }

    async def get_pending_reviews(
        self,
        db: AsyncSession,
        assigned_to: Optional[str] = None,
        item_type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """TR: Bekleyen review'ları getir"""
        try:
            from sqlalchemy import select, and_

            # TR: Query oluştur
            query = select(ReviewItem).where(
                ReviewItem.status == ReviewStatus.PENDING.value
            )

            if assigned_to:
                query = query.where(ReviewItem.assigned_to == assigned_to)

            if item_type:
                query = query.where(ReviewItem.item_type == item_type)

            if priority:
                query = query.where(ReviewItem.priority == priority)

            query = query.order_by(
                ReviewItem.priority.desc(), ReviewItem.created_at.asc()
            )
            query = query.limit(limit)

            result = await db.execute(query)
            review_items = result.scalars().all()

            items_data = []
            for item in review_items:
                items_data.append(
                    {
                        "id": item.id,
                        "item_type": item.item_type,
                        "item_data": item.item_data,
                        "status": item.status,
                        "priority": item.priority,
                        "assigned_to": item.assigned_to,
                        "project_id": item.project_id,
                        "created_by": item.created_by,
                        "created_at": item.created_at.isoformat(),
                        "updated_at": (
                            item.updated_at.isoformat() if item.updated_at else None
                        ),
                    }
                )

            return {
                "success": True,
                "data": {"items": items_data, "count": len(items_data)},
            }

        except Exception as e:
            logger.error(f"TR: Pending reviews getirme hatası: {e}")
            return {
                "success": False,
                "error": f"TR: Pending reviews getirme hatası: {str(e)}",
            }

    async def assign_review(
        self,
        db: AsyncSession,
        item_id: str,
        reviewer_id: str,
        assigned_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """TR: Review'ı atama"""
        try:
            # TR: Review item'ı getir
            review_item = await db.get(ReviewItem, item_id)
            if not review_item:
                return {"success": False, "error": "TR: Review item bulunamadı"}

            # TR: Durum kontrolü
            if review_item.status != ReviewStatus.PENDING.value:
                return {
                    "success": False,
                    "error": f"TR: Review zaten atanmış, mevcut durum: {review_item.status}",
                }

            # TR: Atama yap
            review_item.assigned_to = reviewer_id
            review_item.status = ReviewStatus.IN_REVIEW.value
            review_item.assigned_at = datetime.now()
            review_item.assigned_by = assigned_by

            await db.flush()

            logger.info(f"TR: Review atandı: {item_id} -> {reviewer_id}")

            return {
                "success": True,
                "data": {
                    "id": review_item.id,
                    "assigned_to": review_item.assigned_to,
                    "status": review_item.status,
                    "assigned_at": review_item.assigned_at.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"TR: Review atama hatası: {e}")
            return {"success": False, "error": f"TR: Review atama hatası: {str(e)}"}

    async def submit_review(
        self,
        db: AsyncSession,
        item_id: str,
        reviewer_id: str,
        decision: str,
        comments: Optional[str] = None,
        feedback_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """TR: Review sonucu gönder - P32-T2"""
        try:
            # TR: Review item'ı getir
            review_item = await db.get(ReviewItem, item_id)
            if not review_item:
                return {"success": False, "error": "TR: Review item bulunamadı"}

            # TR: Durum ve atama kontrolü
            if review_item.status != ReviewStatus.IN_REVIEW.value:
                return {
                    "success": False,
                    "error": f"TR: Review beklenen durumda değil: {review_item.status}",
                }

            if review_item.assigned_to != reviewer_id:
                return {"success": False, "error": "TR: Bu review size atanmamış"}

            # TR: Decision validation
            valid_decisions = ["approved", "rejected", "needs_revision"]
            if decision not in valid_decisions:
                return {"success": False, "error": f"TR: Geçersiz karar: {decision}"}

            # TR: Review sonucunu kaydet
            review_item.status = decision
            review_item.reviewed_by = reviewer_id
            review_item.reviewed_at = datetime.now()
            review_item.comments = comments
            review_item.feedback_data = feedback_data or {}

            await db.flush()

            logger.info(f"TR: Review tamamlandı: {item_id} -> {decision}")

            # TR: Feedback loop - P32-T3
            if decision == "needs_revision" and feedback_data:
                await self._process_revision_feedback(db, item_id, feedback_data)

            return {
                "success": True,
                "data": {
                    "id": review_item.id,
                    "status": review_item.status,
                    "decision": decision,
                    "reviewed_at": review_item.reviewed_at.isoformat(),
                    "comments": comments,
                },
            }

        except Exception as e:
            logger.error(f"TR: Review submit hatası: {e}")
            return {"success": False, "error": f"TR: Review submit hatası: {str(e)}"}

    async def _process_revision_feedback(
        self, db: AsyncSession, item_id: str, feedback_data: Dict[str, Any]
    ) -> None:
        """TR: Revision feedback işleme - P32-T3"""
        try:
            # TR: Feedback'i analiz et ve öneriler oluştur
            suggestions = []

            if "geometric_issues" in feedback_data:
                suggestions.append("TR: Geometrik düzenlemeler gerekli")

            if "code_violations" in feedback_data:
                suggestions.append("TR: Bina kodları ihlalleri düzeltilmeli")

            if "design_improvements" in feedback_data:
                suggestions.append("TR: Tasarım iyileştirmeleri önerilir")

            # TR: Feedback'i review item'a kaydet
            review_item = await db.get(ReviewItem, item_id)
            if review_item:
                review_item.feedback_data["suggestions"] = suggestions
                review_item.feedback_data["processed_at"] = datetime.now().isoformat()

                await db.flush()

                logger.info(f"TR: Feedback işlendi: {item_id}")

        except Exception as e:
            logger.error(f"TR: Feedback işleme hatası: {e}")

    async def get_review_statistics(
        self,
        db: AsyncSession,
        reviewer_id: Optional[str] = None,
        project_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """TR: Review istatistikleri getir"""
        try:
            from sqlalchemy import select, func, and_

            # TR: Base query
            query = select(ReviewItem)
            conditions = []

            if reviewer_id:
                conditions.append(ReviewItem.assigned_to == reviewer_id)

            if project_id:
                conditions.append(ReviewItem.project_id == project_id)

            if date_from:
                conditions.append(ReviewItem.created_at >= date_from)

            if date_to:
                conditions.append(ReviewItem.created_at <= date_to)

            if conditions:
                query = query.where(and_(*conditions))

            result = await db.execute(query)
            all_items = result.scalars().all()

            # TR: İstatistikleri hesapla
            total_items = len(all_items)
            status_counts = {}
            priority_counts = {}

            for item in all_items:
                # TR: Status counts
                status = item.status
                status_counts[status] = status_counts.get(status, 0) + 1

                # TR: Priority counts
                priority = item.priority
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            # TR: Approval rate hesapla
            approved_count = status_counts.get("approved", 0)
            rejected_count = status_counts.get("rejected", 0)
            total_reviewed = approved_count + rejected_count
            approval_rate = (
                (approved_count / total_reviewed) if total_reviewed > 0 else 0.0
            )

            return {
                "success": True,
                "data": {
                    "total_items": total_items,
                    "status_distribution": status_counts,
                    "priority_distribution": priority_counts,
                    "approval_rate": approval_rate,
                    "reviewed_items": total_reviewed,
                    "pending_items": status_counts.get("pending", 0),
                    "in_review_items": status_counts.get("in_review", 0),
                },
            }

        except Exception as e:
            logger.error(f"TR: Review istatistikleri hatası: {e}")
            return {
                "success": False,
                "error": f"TR: Review istatistikleri hatası: {str(e)}",
            }

    async def get_review_history(
        self, db: AsyncSession, item_id: str
    ) -> Dict[str, Any]:
        """TR: Review geçmişi getir"""
        try:
            review_item = await db.get(ReviewItem, item_id)
            if not review_item:
                return {"success": False, "error": "TR: Review item bulunamadı"}

            history_data = {
                "id": review_item.id,
                "item_type": review_item.item_type,
                "status": review_item.status,
                "priority": review_item.priority,
                "created_at": review_item.created_at.isoformat(),
                "created_by": review_item.created_by,
                "assigned_to": review_item.assigned_to,
                "assigned_at": (
                    review_item.assigned_at.isoformat()
                    if review_item.assigned_at
                    else None
                ),
                "assigned_by": review_item.assigned_by,
                "reviewed_by": review_item.reviewed_by,
                "reviewed_at": (
                    review_item.reviewed_at.isoformat()
                    if review_item.reviewed_at
                    else None
                ),
                "comments": review_item.comments,
                "feedback_data": review_item.feedback_data,
            }

            return {"success": True, "data": history_data}

        except Exception as e:
            logger.error(f"TR: Review history hatası: {e}")
            return {"success": False, "error": f"TR: Review history hatası: {str(e)}"}
