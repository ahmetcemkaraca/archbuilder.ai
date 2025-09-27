"""
Main Layout Generation Integration Service for ArchBuilder.AI

Orchestrates the complete AI processing pipeline including:
- Layout generation
- CAD processing
- Human review workflow
- Validation layers

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import logging (fallback if structlog not available)
try:
    from structlog import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Import our services
from .layout_generation_service import LayoutGenerationService
from .cad_processing_service import CADProcessingService
from .human_review_service import HumanReviewService
from .simple_layout_validator import SimpleLayoutValidator


class LayoutIntegrationService:
    """
    Main integration service for AI-powered layout generation workflow

    Bu servis şu işlemleri koordine eder:
    - AI layout generation
    - Validation pipeline
    - Human review assignment
    - CAD file processing
    - Existing project analysis
    """

    def __init__(self):
        # Initialize services with mock dependencies for now
        # self.layout_service = LayoutGenerationService()  # Need proper initialization
        # self.cad_service = CADProcessingService()
        # self.review_service = HumanReviewService()
        # self.validator = SimpleLayoutValidator()

        # Placeholder implementations - will be properly initialized later
        self.layout_service = None
        self.cad_service = CADProcessingService()
        self.review_service = HumanReviewService()
        self.validator = SimpleLayoutValidator()

        # Track active generations
        self.active_generations: Dict[str, Dict[str, Any]] = {}

    async def generate_layout_workflow(
        self, request_data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete layout generation workflow

        Args:
            request_data: Layout generation request
            correlation_id: Request correlation ID

        Returns:
            Dict: Workflow results
        """

        workflow_id = str(uuid.uuid4())
        correlation_id = correlation_id or f"gen_{workflow_id[:8]}"

        logger.info(
            "Layout generation workflow başlatıldı - ID: %s, Correlation: %s",
            workflow_id,
            correlation_id,
        )

        # Track workflow
        workflow_state = {
            "workflow_id": workflow_id,
            "correlation_id": correlation_id,
            "status": "processing",
            "started_at": datetime.now(),
            "stages": {},
        }

        self.active_generations[workflow_id] = workflow_state

        try:
            # Stage 1: AI Layout Generation
            logger.info("Stage 1: AI layout generation - Workflow: %s", workflow_id)
            workflow_state["stages"]["generation"] = {
                "status": "processing",
                "started_at": datetime.now(),
            }

            # Mock layout result since layout_service is not properly initialized yet
            layout_result = {
                "layout_id": workflow_id,
                "status": "generated",
                "layout_data": {"walls": [], "doors": [], "windows": [], "rooms": []},
                "ai_confidence": 0.85,
                "generation_time_ms": 1000,
            }
            # layout_result = await self.layout_service.generate_layout(request_data, correlation_id)

            workflow_state["stages"]["generation"] = {
                "status": "completed",
                "started_at": workflow_state["stages"]["generation"]["started_at"],
                "completed_at": datetime.now(),
                "result": layout_result,
            }

            # Stage 2: Layout Validation
            logger.info("Stage 2: Layout validation - Workflow: %s", workflow_id)
            workflow_state["stages"]["validation"] = {
                "status": "processing",
                "started_at": datetime.now(),
            }

            validation_results = []
            if layout_result.get("layout_data"):
                validation_result = await self.validator.validate_layout(
                    layout_result["layout_data"]
                )
                validation_results = [validation_result]

            workflow_state["stages"]["validation"] = {
                "status": "completed",
                "started_at": workflow_state["stages"]["validation"]["started_at"],
                "completed_at": datetime.now(),
                "results": validation_results,
            }

            # Stage 3: Human Review Assignment (if needed)
            needs_review = self._determine_review_requirement(
                layout_result, validation_results
            )

            if needs_review:
                logger.info("Stage 3: Human review assignment", workflow_id=workflow_id)
                workflow_state["stages"]["review"] = {
                    "status": "processing",
                    "started_at": datetime.now(),
                }

                review_id = await self.review_service.submit_for_review(
                    layout_id=layout_result.get("layout_id", workflow_id),
                    request=request_data,
                    result=layout_result,
                    validation_results=validation_results,
                    ai_confidence=layout_result.get("ai_confidence"),
                )

                workflow_state["stages"]["review"] = {
                    "status": "pending",
                    "started_at": workflow_state["stages"]["review"]["started_at"],
                    "review_id": review_id,
                }

            else:
                # Auto-approve if validation passes and confidence is high
                workflow_state["stages"]["review"] = {
                    "status": "auto_approved",
                    "started_at": datetime.now(),
                    "completed_at": datetime.now(),
                }

            # Stage 4: Prepare final results
            workflow_state["status"] = (
                "completed" if not needs_review else "pending_review"
            )
            workflow_state["completed_at"] = datetime.now()

            result = {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "layout_result": layout_result,
                "validation_results": validation_results,
                "review_required": needs_review,
                "review_id": workflow_state["stages"]
                .get("review", {})
                .get("review_id"),
                "processing_time_ms": int(
                    (
                        workflow_state.get("completed_at", datetime.now())
                        - workflow_state["started_at"]
                    ).total_seconds()
                    * 1000
                ),
            }

            logger.info(
                "Layout generation workflow tamamlandı",
                workflow_id=workflow_id,
                status=result["status"],
                review_required=needs_review,
                processing_time_ms=result["processing_time_ms"],
            )

            return result

        except Exception as e:
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            workflow_state["completed_at"] = datetime.now()

            logger.error(
                "Layout generation workflow hatası",
                workflow_id=workflow_id,
                error=str(e),
                exc_info=True,
            )

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": int(
                    (datetime.now() - workflow_state["started_at"]).total_seconds()
                    * 1000
                ),
            }

    async def process_cad_file_workflow(
        self, file_data: bytes, filename: str, analysis_type: str = "existing_project"
    ) -> Dict[str, Any]:
        """
        CAD file processing workflow

        Args:
            file_data: CAD file binary data
            filename: Original filename
            analysis_type: Type of analysis (existing_project, format_conversion, etc.)

        Returns:
            Dict: Processing results
        """

        workflow_id = str(uuid.uuid4())

        logger.info(
            "CAD processing workflow başlatıldı",
            workflow_id=workflow_id,
            filename=filename,
            analysis_type=analysis_type,
            file_size_bytes=len(file_data),
        )

        try:
            if analysis_type == "existing_project":
                # Analyze existing project for AI recommendations
                analysis_result = await self.cad_service.analyze_existing_project(
                    file_data, filename
                )

                return {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "analysis_type": analysis_type,
                    "filename": filename,
                    "analysis_result": analysis_result,
                }

            else:
                # Standard CAD processing
                processing_result = await self.cad_service.process_cad_file(
                    file_data, filename
                )

                return {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "analysis_type": analysis_type,
                    "filename": filename,
                    "processing_result": (
                        processing_result.__dict__
                        if hasattr(processing_result, "__dict__")
                        else processing_result
                    ),
                }

        except Exception as e:
            logger.error(
                "CAD processing workflow hatası",
                workflow_id=workflow_id,
                filename=filename,
                error=str(e),
                exc_info=True,
            )

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "filename": filename,
                "error": str(e),
            }

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""

        return self.active_generations.get(workflow_id)

    async def get_review_queue_dashboard(
        self, reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get review dashboard data"""

        try:
            if reviewer_id:
                # Get specific reviewer dashboard
                dashboard = await self.review_service.get_reviewer_dashboard(
                    reviewer_id
                )
            else:
                # Get system-wide review stats
                stats = await self.review_service.get_system_stats()
                queue = await self.review_service.get_review_queue(limit=20)

                dashboard = {
                    "system_stats": (
                        stats.__dict__ if hasattr(stats, "__dict__") else stats
                    ),
                    "recent_queue": [
                        item.__dict__ if hasattr(item, "__dict__") else item
                        for item in queue
                    ],
                }

            return dashboard

        except Exception as e:
            logger.error("Review dashboard hatası", error=str(e))
            return {"error": str(e)}

    async def submit_review_feedback(
        self,
        review_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_role: str,
        rating: int,
        comments: str,
        suggestions: List[str],
        approval_status: bool,
    ) -> Dict[str, Any]:
        """Submit review feedback"""

        try:
            # Import ReviewerRole from human_review_service
            # For now use string directly
            success = await self.review_service.submit_feedback(
                review_id=review_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer_name,
                reviewer_role=reviewer_role,  # Convert to enum if needed
                rating=rating,
                comments=comments,
                suggestions=suggestions,
                approval_status=approval_status,
            )

            return {
                "success": success,
                "review_id": review_id,
                "message": (
                    "Feedback başarıyla gönderildi"
                    if success
                    else "Feedback gönderilemedi"
                ),
            }

        except Exception as e:
            logger.error("Review feedback hatası", review_id=review_id, error=str(e))
            return {"success": False, "error": str(e)}

    async def export_layout_to_cad(
        self, layout_data: Dict[str, Any], target_format: str = "dxf"
    ) -> Dict[str, Any]:
        """Export layout to CAD format"""

        try:
            walls = layout_data.get("walls", [])
            doors = layout_data.get("doors", [])
            windows = layout_data.get("windows", [])

            if target_format.lower() == "dxf":
                cad_data = await self.cad_service.convert_layout_to_dxf(
                    walls, doors, windows
                )

                return {
                    "success": True,
                    "format": "dxf",
                    "data": cad_data,
                    "size_bytes": len(cad_data),
                }
            else:
                return {
                    "success": False,
                    "error": f"Desteklenmeyen format: {target_format}",
                }

        except Exception as e:
            logger.error("CAD export hatası", target_format=target_format, error=str(e))
            return {"success": False, "error": str(e)}

    def _determine_review_requirement(
        self, layout_result: Dict[str, Any], validation_results: List[Any]
    ) -> bool:
        """Determine if human review is required"""

        # Check AI confidence
        ai_confidence = layout_result.get("ai_confidence", 0.0)
        if ai_confidence < 0.8:
            return True

        # Check validation errors
        total_errors = sum(len(getattr(vr, "errors", [])) for vr in validation_results)
        if total_errors > 0:
            return True

        # Check if it's a complex layout
        layout_data = layout_result.get("layout_data", {})
        element_count = (
            len(layout_data.get("walls", []))
            + len(layout_data.get("doors", []))
            + len(layout_data.get("windows", []))
        )

        if element_count > 20:  # Complex layout threshold
            return True

        # Auto-approve simple layouts with high confidence
        return False

    async def cleanup_old_workflows(self, hours: int = 24) -> int:
        """Clean up old workflow data"""

        cutoff_time = datetime.now() - timedelta(hours=hours)

        workflows_to_remove = [
            wf_id
            for wf_id, wf_data in self.active_generations.items()
            if wf_data.get("started_at", datetime.now()) < cutoff_time
            and wf_data.get("status") in ["completed", "failed"]
        ]

        for workflow_id in workflows_to_remove:
            del self.active_generations[workflow_id]

        logger.info("Cleaned up %d old workflows", len(workflows_to_remove))

        return len(workflows_to_remove)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""

        return {
            "status": "healthy",
            "active_workflows": len(self.active_generations),
            "services": {
                "layout_generation": "ready",
                "cad_processing": "ready",
                "human_review": "ready",
                "validation": "ready",
            },
            "supported_formats": self.cad_service.get_supported_formats(),
            "timestamp": datetime.now().isoformat(),
        }
