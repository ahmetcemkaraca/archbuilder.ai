"""
Simple Layout Validator for ArchBuilder.AI

Basic validation service with minimal dependencies for AI pipeline testing.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import math
from datetime import datetime
from typing import Dict, List, Any


# Import logging (fallback if structlog not available)
try:
    from structlog import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class SimpleValidationError:
    """Simple validation error class"""

    def __init__(
        self,
        code: str,
        message: str,
        severity: str = "error",
        location: str = None,
        suggestion: str = None,
    ):
        self.code = code
        self.message = message
        self.severity = severity  # "error" or "warning"
        self.location = location
        self.suggestion = suggestion


class SimpleValidationResult:
    """Simple validation result class"""

    def __init__(self):
        self.errors: List[SimpleValidationError] = []
        self.warnings: List[SimpleValidationError] = []
        self.is_valid: bool = True
        self.confidence: float = 1.0
        self.validated_at: datetime = datetime.now()


class SimpleLayoutValidator:
    """
    Simple layout validator with basic checks

    Bu validator şu temel kontrolleri yapar:
    - Wall connectivity ve dimensions
    - Door/window placement validation
    - Room area calculations
    - Basic accessibility checks
    """

    def __init__(self):
        pass

    async def validate_layout(
        self, layout_data: Dict[str, Any]
    ) -> SimpleValidationResult:
        """
        Layout validation - basic implementation

        Args:
            layout_data: Dict containing walls, doors, windows, rooms

        Returns:
            SimpleValidationResult: Validation results
        """

        logger.info("Layout validation başlatıldı")

        result = SimpleValidationResult()

        try:
            # Get layout components
            walls = layout_data.get('walls', [])
            doors = layout_data.get('doors', [])
            windows = layout_data.get('windows', [])
            rooms = layout_data.get('rooms', [])

            # Basic validation checks
            await self._validate_walls(walls, result)
            await self._validate_doors(doors, walls, result)
            await self._validate_windows(windows, walls, result)
            await self._validate_rooms(rooms, result)

            # Calculate overall validation status
            result.is_valid = len(result.errors) == 0
            result.confidence = max(
                0.0, 1.0 - (len(result.errors) * 0.2) - (len(result.warnings) * 0.1)
            )

            logger.info(
                "Layout validation tamamlandı - Valid: %s, Errors: %d, Warnings: %d, Confidence: %.2f",
                result.is_valid,
                len(result.errors),
                len(result.warnings),
                result.confidence,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error("Layout validation hatası: %s", str(e))
            result.errors.append(
                SimpleValidationError(
                    code="VALIDATION_ERROR",
                    message=f"Validation işlemi başarısız: {str(e)}",
                    severity="error",
                )
            )
            result.is_valid = False
            result.confidence = 0.0

        return result

    async def _validate_walls(
        self, walls: List[Dict[str, Any]], result: SimpleValidationResult
    ):
        """Wall validation"""

        if not walls:
            result.warnings.append(
                SimpleValidationError(
                    code="NO_WALLS",
                    message="Duvar elemanı bulunamadı",
                    severity="warning",
                    suggestion="Layout'a duvar elemanları ekleyin",
                )
            )
            return

        for i, wall in enumerate(walls):
            # Check wall structure
            if 'start' not in wall or 'end' not in wall:
                result.errors.append(
                    SimpleValidationError(
                        code="INVALID_WALL_STRUCTURE",
                        message=f"Duvar {i}: Başlangıç veya bitiş noktası eksik",
                        severity="error",
                        location=f"wall[{i}]",
                    )
                )
                continue

            # Check wall dimensions
            start = wall['start']
            end = wall['end']

            if 'x' not in start or 'y' not in start or 'x' not in end or 'y' not in end:
                result.errors.append(
                    SimpleValidationError(
                        code="INVALID_COORDINATES",
                        message=f"Duvar {i}: Geçersiz koordinat bilgisi",
                        severity="error",
                        location=f"wall[{i}]",
                    )
                )
                continue

            # Calculate wall length
            dx = end['x'] - start['x']
            dy = end['y'] - start['y']
            length = math.sqrt(dx * dx + dy * dy)

            if length < 100:  # Minimum 10cm
                result.errors.append(
                    SimpleValidationError(
                        code="WALL_TOO_SHORT",
                        message=f"Duvar {i}: Çok kısa duvar ({length:.0f}mm)",
                        severity="error",
                        location=f"wall[{i}]",
                        suggestion="Duvar uzunluğu minimum 100mm olmalıdır",
                    )
                )

            if length > 20000:  # Maximum 20m
                result.warnings.append(
                    SimpleValidationError(
                        code="WALL_TOO_LONG",
                        message=f"Duvar {i}: Çok uzun duvar ({length:.0f}mm)",
                        severity="warning",
                        location=f"wall[{i}]",
                        suggestion="Uzun duvarları bölmeyi düşünün",
                    )
                )

    async def _validate_doors(
        self,
        doors: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        result: SimpleValidationResult,
    ):
        """Door validation"""

        for i, door in enumerate(doors):
            # Check door structure
            required_fields = ['wall_index', 'position', 'width']
            for field in required_fields:
                if field not in door:
                    result.errors.append(
                        SimpleValidationError(
                            code="INVALID_DOOR_STRUCTURE",
                            message=f"Kapı {i}: {field} bilgisi eksik",
                            severity="error",
                            location=f"door[{i}]",
                        )
                    )
                    continue

            # Check wall index
            wall_index = door.get('wall_index', -1)
            if wall_index < 0 or wall_index >= len(walls):
                result.errors.append(
                    SimpleValidationError(
                        code="INVALID_WALL_INDEX",
                        message=f"Kapı {i}: Geçersiz duvar indeksi {wall_index}",
                        severity="error",
                        location=f"door[{i}]",
                    )
                )
                continue

            # Check door width
            door_width = door.get('width', 0)
            if door_width < 600:
                result.errors.append(
                    SimpleValidationError(
                        code="DOOR_TOO_NARROW",
                        message=f"Kapı {i}: Kapı çok dar ({door_width}mm)",
                        severity="error",
                        location=f"door[{i}]",
                        suggestion="Kapı genişliği minimum 600mm olmalıdır",
                    )
                )

            if door_width < 800:
                result.warnings.append(
                    SimpleValidationError(
                        code="DOOR_ACCESSIBILITY",
                        message=f"Kapı {i}: Engelli erişimi için dar ({door_width}mm)",
                        severity="warning",
                        location=f"door[{i}]",
                        suggestion="Engelli erişimi için minimum 800mm önerilir",
                    )
                )

    async def _validate_windows(
        self,
        windows: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        result: SimpleValidationResult,
    ):
        """Window validation"""

        for i, window in enumerate(windows):
            # Check window structure
            required_fields = ['wall_index', 'position', 'width', 'height']
            for field in required_fields:
                if field not in window:
                    result.errors.append(
                        SimpleValidationError(
                            code="INVALID_WINDOW_STRUCTURE",
                            message=f"Pencere {i}: {field} bilgisi eksik",
                            severity="error",
                            location=f"window[{i}]",
                        )
                    )
                    continue

            # Check wall index
            wall_index = window.get('wall_index', -1)
            if wall_index < 0 or wall_index >= len(walls):
                result.errors.append(
                    SimpleValidationError(
                        code="INVALID_WALL_INDEX",
                        message=f"Pencere {i}: Geçersiz duvar indeksi {wall_index}",
                        severity="error",
                        location=f"window[{i}]",
                    )
                )
                continue

            # Check window dimensions
            window_width = window.get('width', 0)
            window_height = window.get('height', 0)

            if window_width < 400:
                result.warnings.append(
                    SimpleValidationError(
                        code="WINDOW_TOO_NARROW",
                        message=f"Pencere {i}: Pencere dar ({window_width}mm)",
                        severity="warning",
                        location=f"window[{i}]",
                        suggestion="Doğal ışık için daha geniş pencere düşünün",
                    )
                )

            if window_height < 600:
                result.warnings.append(
                    SimpleValidationError(
                        code="WINDOW_TOO_SHORT",
                        message=f"Pencere {i}: Pencere kısa ({window_height}mm)",
                        severity="warning",
                        location=f"window[{i}]",
                        suggestion="Daha iyi manzara için daha uzun pencere düşünün",
                    )
                )

    async def _validate_rooms(
        self, rooms: List[Dict[str, Any]], result: SimpleValidationResult
    ):
        """Room validation"""

        if not rooms:
            result.warnings.append(
                SimpleValidationError(
                    code="NO_ROOMS",
                    message="Oda tanımı bulunamadı",
                    severity="warning",
                    suggestion="Layout'a oda tanımları ekleyin",
                )
            )
            return

        for i, room in enumerate(rooms):
            # Check room structure
            if 'name' not in room:
                result.warnings.append(
                    SimpleValidationError(
                        code="ROOM_NO_NAME",
                        message=f"Oda {i}: Oda adı eksik",
                        severity="warning",
                        location=f"room[{i}]",
                    )
                )

            # Check room area
            room_area = room.get('area', 0)
            if room_area < 5.0:  # Minimum 5m²
                result.warnings.append(
                    SimpleValidationError(
                        code="ROOM_TOO_SMALL",
                        message=f"Oda {i}: Oda çok küçük ({room_area:.1f}m²)",
                        severity="warning",
                        location=f"room[{i}]",
                        suggestion="Minimum oda alanı 5m² olmalıdır",
                    )
                )

            if room_area > 100.0:  # Maximum 100m² warning
                result.warnings.append(
                    SimpleValidationError(
                        code="ROOM_VERY_LARGE",
                        message=f"Oda {i}: Oda çok büyük ({room_area:.1f}m²)",
                        severity="warning",
                        location=f"room[{i}]",
                        suggestion="Büyük odaları bölmeyi düşünün",
                    )
                )

    def get_validation_summary(self, result: SimpleValidationResult) -> Dict[str, Any]:
        """Validation summary for reporting"""

        return {
            "is_valid": result.is_valid,
            "confidence": result.confidence,
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
            "error_codes": [e.code for e in result.errors],
            "warning_codes": [w.code for w in result.warnings],
            "validated_at": result.validated_at.isoformat(),
        }
