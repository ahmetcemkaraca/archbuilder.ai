"""
Celery Background Task Queue for ArchBuilder.AI

Provides:
- Long-running task processing
- AI model inference queues
- Document processing pipelines
- Email notifications
- Scheduled tasks
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from celery import Celery, Task
from celery.schedules import crontab
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status states"""

    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskType(str, Enum):
    """Task type categories"""

    AI_INFERENCE = "ai_inference"
    DOCUMENT_PROCESSING = "document_processing"
    EMAIL_NOTIFICATION = "email_notification"
    DATA_ANALYSIS = "data_analysis"
    CLEANUP = "cleanup"
    HEALTH_CHECK = "health_check"


class TaskRequest(BaseModel):
    """Task request model"""

    task_id: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    correlation_id: str
    user_id: str
    payload: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes default
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResult(BaseModel):
    """Task result model"""

    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    retry_count: int = 0


class ArchBuilderTask(Task):
    """Base task class for ArchBuilder.AI with enhanced monitoring"""

    def on_success(self, retval, task_id, args, kwargs):
        """Task success callback"""
        logger.info(
            "Task completed successfully",
            task_id=task_id,
            task_name=self.name,
            result_type=type(retval).__name__,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Task failure callback"""
        logger.error(
            "Task failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            error_info=str(einfo),
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Task retry callback"""
        logger.warning(
            "Task retrying",
            task_id=task_id,
            task_name=self.name,
            retry_count=self.request.retries,
            max_retries=self.max_retries,
            error=str(exc),
        )


# Celery app configuration
celery_app = Celery(
    "archbuilder",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
    include=[
        "app.core.tasks.ai_tasks",
        "app.core.tasks.document_tasks",
        "app.core.tasks.notification_tasks",
        "app.core.tasks.cleanup_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.core.tasks.ai_tasks.*": {"queue": "ai_inference"},
        "app.core.tasks.document_tasks.*": {"queue": "document_processing"},
        "app.core.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.core.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    # Queue configuration
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "ai_inference": {"exchange": "ai_inference", "routing_key": "ai_inference"},
        "document_processing": {
            "exchange": "document_processing",
            "routing_key": "document_processing",
        },
        "notifications": {"exchange": "notifications", "routing_key": "notifications"},
        "cleanup": {"exchange": "cleanup", "routing_key": "cleanup"},
    },
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    task_retry_jitter=True,
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.core.tasks.cleanup_tasks.cleanup_old_tasks",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "health-check": {
            "task": "app.core.tasks.health_tasks.system_health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-temp-files": {
            "task": "app.core.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "generate-usage-reports": {
            "task": "app.core.tasks.analytics_tasks.generate_usage_reports",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
        },
    },
)


class TaskQueueManager:
    """High-level task queue manager for ArchBuilder.AI"""

    def __init__(self):
        self.celery_app = celery_app

    async def submit_ai_inference_task(
        self,
        correlation_id: str,
        user_id: str,
        model: str,
        prompt: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """Submit AI inference task to queue"""
        task_request = TaskRequest(
            task_id=f"ai_{correlation_id}",
            task_type=TaskType.AI_INFERENCE,
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            payload={"model": model, "prompt": prompt, "context": context},
        )

        # Submit to AI inference queue
        task = self.celery_app.send_task(
            "app.core.tasks.ai_tasks.process_ai_inference",
            args=[task_request.dict()],
            queue="ai_inference",
            priority=self._get_priority_value(priority),
        )

        logger.info(
            "AI inference task submitted",
            task_id=task.id,
            correlation_id=correlation_id,
            model=model,
            priority=priority.value,
        )

        return task.id

    async def submit_document_processing_task(
        self,
        correlation_id: str,
        user_id: str,
        document_id: str,
        processing_type: str,
        options: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """Submit document processing task to queue"""
        task_request = TaskRequest(
            task_id=f"doc_{correlation_id}",
            task_type=TaskType.DOCUMENT_PROCESSING,
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            payload={
                "document_id": document_id,
                "processing_type": processing_type,
                "options": options,
            },
        )

        # Submit to document processing queue
        task = self.celery_app.send_task(
            "app.core.tasks.document_tasks.process_document",
            args=[task_request.dict()],
            queue="document_processing",
            priority=self._get_priority_value(priority),
        )

        logger.info(
            "Document processing task submitted",
            task_id=task.id,
            correlation_id=correlation_id,
            document_id=document_id,
            processing_type=processing_type,
        )

        return task.id

    async def submit_notification_task(
        self,
        correlation_id: str,
        user_id: str,
        notification_type: str,
        recipient: str,
        content: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """Submit notification task to queue"""
        task_request = TaskRequest(
            task_id=f"notif_{correlation_id}",
            task_type=TaskType.EMAIL_NOTIFICATION,
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            payload={
                "notification_type": notification_type,
                "recipient": recipient,
                "content": content,
            },
        )

        # Submit to notifications queue
        task = self.celery_app.send_task(
            "app.core.tasks.notification_tasks.send_notification",
            args=[task_request.dict()],
            queue="notifications",
            priority=self._get_priority_value(priority),
        )

        logger.info(
            "Notification task submitted",
            task_id=task.id,
            correlation_id=correlation_id,
            notification_type=notification_type,
            recipient=recipient,
        )

        return task.id

    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status and result"""
        try:
            result = self.celery_app.AsyncResult(task_id)

            if result.state == "PENDING":
                status = TaskStatus.PENDING
            elif result.state == "STARTED":
                status = TaskStatus.STARTED
            elif result.state == "SUCCESS":
                status = TaskStatus.SUCCESS
            elif result.state == "FAILURE":
                status = TaskStatus.FAILURE
            elif result.state == "RETRY":
                status = TaskStatus.RETRY
            elif result.state == "REVOKED":
                status = TaskStatus.REVOKED
            else:
                status = TaskStatus.PENDING

            return TaskResult(
                task_id=task_id,
                status=status,
                result=result.result if result.successful() else None,
                error=str(result.result) if result.failed() else None,
                completed_at=datetime.utcnow() if result.ready() else None,
            )

        except Exception as e:
            logger.error("Failed to get task status", task_id=task_id, error=str(e))
            return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info("Task cancelled", task_id=task_id)
            return True
        except Exception as e:
            logger.error("Failed to cancel task", task_id=task_id, error=str(e))
            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            inspect = self.celery_app.control.inspect()

            # Get active tasks
            active_tasks = inspect.active()

            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled()

            # Get reserved tasks
            reserved_tasks = inspect.reserved()

            # Get queue lengths
            queue_stats = {}
            for queue_name in [
                "default",
                "ai_inference",
                "document_processing",
                "notifications",
                "cleanup",
            ]:
                queue_stats[queue_name] = {
                    "active": len(active_tasks.get(queue_name, [])),
                    "scheduled": len(scheduled_tasks.get(queue_name, [])),
                    "reserved": len(reserved_tasks.get(queue_name, [])),
                }

            return {
                "queues": queue_stats,
                "total_active": sum(len(tasks) for tasks in active_tasks.values()),
                "total_scheduled": sum(
                    len(tasks) for tasks in scheduled_tasks.values()
                ),
                "total_reserved": sum(len(tasks) for tasks in reserved_tasks.values()),
            }

        except Exception as e:
            logger.error("Failed to get queue stats", error=str(e))
            return {}

    def _get_priority_value(self, priority: TaskPriority) -> int:
        """Convert priority enum to numeric value"""
        priority_map = {
            TaskPriority.LOW: 0,
            TaskPriority.NORMAL: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.CRITICAL: 3,
        }
        return priority_map.get(priority, 1)


# Global task queue manager
_task_queue_manager: Optional[TaskQueueManager] = None


def initialize_task_queue() -> TaskQueueManager:
    """Initialize global task queue manager"""
    global _task_queue_manager

    _task_queue_manager = TaskQueueManager()
    return _task_queue_manager


def get_task_queue_manager() -> TaskQueueManager:
    """Get global task queue manager instance"""
    if _task_queue_manager is None:
        raise RuntimeError("Task queue manager not initialized")
    return _task_queue_manager


# Celery worker health check
@celery_app.task(bind=True, base=ArchBuilderTask)
def health_check_task(self):
    """Health check task for monitoring worker status"""
    return {
        "status": "healthy",
        "worker_id": self.request.hostname,
        "timestamp": datetime.utcnow().isoformat(),
    }
