"""
Comprehensive Layout Validator for ArchBuilder.AI

Multi-layer validation system for AI-generated architectural layouts:
- Geometric validation (overlaps, dimensions, connectivity)
- Spatial validation (room sizes, accessibility)
- Building code validation (Turkish regulations)
- Safety and compliance checks

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import math
from typing import Dict, List, Tuple, Any
from enum import Enum

# Import logging (fallback if structlog not available)
try:
    from structlog import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Placeholder imports - adjust based on actual package structure
# from ..schemas.layout_schemas import (
#     LayoutData, ValidationResult, ValidationError, ValidationStatus
# )
# from ..utils.geometry import GeometryUtils
# from ..utils.building_codes import TurkishBuildingCodeValidator


class ErrorSeverity(str, Enum):
    """Hata önem dereceleri"""

    CRITICAL = "critical"  # Kesinlikle düzeltilmeli
    ERROR = "error"  # Düzeltilmesi gereken
    WARNING = "warning"  # Dikkat edilmesi gereken
    INFO = "info"  # Bilgilendirme


class ComprehensiveLayoutValidator:
    """
    Comprehensive architectural layout validation service

    Bu servis şu validation katmanlarını içerir:
    1. Schema validation (JSON structure)
    2. Geometric validation (overlaps, dimensions)
    3. Spatial validation (room sizes, accessibility)
    4. Building code validation (Turkish regulations)
    5. Safety validation (fire exits, structural)
    """

    def __init__(self):
        # TR: Initialize geometry utilities and building code validator
        # self.geometry_utils = GeometryUtils()  # Will be available when imported
        # self.building_code_validator = TurkishBuildingCodeValidator()  # Will be available when imported
        
        # TR: Temporary mock implementations until dependencies are available
        self.geometry_utils = self._create_geometry_utils_mock()
        self.building_code_validator = self._create_building_code_validator_mock()
        
        self.min_room_area = 5.0  # m²
        self.min_corridor_width = 1200  # mm
        self.min_door_width = 800  # mm
        self.max_door_width = 1200  # mm
        self.min_window_area_ratio = 0.125  # 1/8 of floor area

    def _create_geometry_utils_mock(self):
        """TR: Temporary mock for geometry utilities"""
        class GeometryUtilsMock:
            def lines_overlap(self, line1, line2):
                # TR: Basic overlap detection - placeholder implementation
                return False
            
            def distance(self, point1, point2):
                # TR: Basic distance calculation - placeholder implementation
                import math
                return math.sqrt((point2.x - point1.x)**2 + (point2.y - point1.y)**2)
        
        return GeometryUtilsMock()
    
    def _create_building_code_validator_mock(self):
        """TR: Temporary mock for building code validator"""
        class BuildingCodeValidatorMock:
            async def validate_layout(self, layout):
                # TR: Placeholder implementation - returns empty results
                return {"errors": [], "warnings": []}
        
        return BuildingCodeValidatorMock()

    async def validate_layout(
        self, layout_data: Dict[str, Any]
    ) -> Any:  # ValidationResult
        """
        Ana validation metodu - tüm katmanları uygular

        Args:
            layout_data: AI tarafından oluşturulan layout data

        Returns:
            ValidationResult: Kapsamlı validation sonucu
        """
        logger.info("Layout validation başlatıldı")

        all_errors = []
        all_warnings = []

        try:
            # Parse layout data
            layout = LayoutData(**layout_data)

            # Layer 1: Geometric validation
            geo_errors, geo_warnings = await self._validate_geometry(layout)
            all_errors.extend(geo_errors)
            all_warnings.extend(geo_warnings)

            # Layer 2: Spatial validation
            spatial_errors, spatial_warnings = await self._validate_spatial_constraints(
                layout
            )
            all_errors.extend(spatial_errors)
            all_warnings.extend(spatial_warnings)

            # Layer 3: Building code validation
            code_errors, code_warnings = await self._validate_building_codes(layout)
            all_errors.extend(code_errors)
            all_warnings.extend(code_warnings)

            # Layer 4: Safety validation
            safety_errors, safety_warnings = await self._validate_safety_requirements(
                layout
            )
            all_errors.extend(safety_errors)
            all_warnings.extend(safety_warnings)

            # Layer 5: Accessibility validation
            access_errors, access_warnings = await self._validate_accessibility(layout)
            all_errors.extend(access_errors)
            all_warnings.extend(access_warnings)

            # Determine overall status
            status = self._determine_validation_status(all_errors, all_warnings)

            # Calculate confidence and compliance scores
            confidence = self._calculate_confidence_score(
                layout, all_errors, all_warnings
            )
            compliance_score = self._calculate_compliance_score(
                all_errors, all_warnings
            )

            # Determine if human review is required
            requires_review = self._requires_human_review(
                status, confidence, all_errors
            )

            result = ValidationResult(
                status=status,
                errors=all_errors,
                warnings=all_warnings,
                confidence=confidence,
                requires_human_review=requires_review,
                compliance_score=compliance_score,
            )

            logger.info(
                "Layout validation tamamlandı",
                status=status.value,
                error_count=len(all_errors),
                warning_count=len(all_warnings),
                confidence=confidence,
                requires_review=requires_review,
            )

            return result

        except Exception as e:
            logger.error("Validation error", error=str(e), exc_info=True)

            return ValidationResult(
                status=ValidationStatus.REJECTED,
                errors=[
                    ValidationError(
                        code="VALIDATION_FAILED",
                        message=f"Validation process failed: {str(e)}",
                        severity=ErrorSeverity.CRITICAL.value,
                    )
                ],
                warnings=[],
                confidence=0.0,
                requires_human_review=True,
                compliance_score=0.0,
            )

    async def _validate_geometry(
        self, layout: LayoutData
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Geometrik validation - duvar çakışmaları, boyutlar vb."""

        errors = []
        warnings = []

        # Wall validation
        for i, wall in enumerate(layout.walls):
            # Check wall length
            # Calculate distance using simple math
            dx = wall["end"]["x"] - wall["start"]["x"]
            dy = wall["end"]["y"] - wall["start"]["y"]
            length = math.sqrt(dx * dx + dy * dy)
            if length < 100:  # 10cm minimum
                errors.append(
                    ValidationError(
                        code="WALL_TOO_SHORT",
                        message=f"Duvar {i+1} çok kısa: {length:.0f}mm (minimum 100mm)",
                        severity=ErrorSeverity.ERROR.value,
                        location=f"Duvar {i+1}",
                        suggestion="Duvar uzunluğunu artırın veya kaldırın",
                    )
                )

            # Check for zero-length walls
            if length == 0:
                errors.append(
                    ValidationError(
                        code="ZERO_LENGTH_WALL",
                        message=f"Duvar {i+1} sıfır uzunlukta",
                        severity=ErrorSeverity.CRITICAL.value,
                        location=f"Duvar {i+1}",
                    )
                )

            # Check wall height
            if wall.height < 2200:
                errors.append(
                    ValidationError(
                        code="WALL_HEIGHT_LOW",
                        message=f"Duvar {i+1} yüksekliği düşük: {wall.height}mm (minimum 2200mm)",
                        severity=ErrorSeverity.ERROR.value,
                        location=f"Duvar {i+1}",
                    )
                )

            # Check for overlapping walls
            for j, other_wall in enumerate(layout.walls[i + 1 :], i + 1):
                if self.geometry_utils.lines_overlap(
                    (wall.start, wall.end), (other_wall.start, other_wall.end)
                ):
                    errors.append(
                        ValidationError(
                            code="WALLS_OVERLAP",
                            message=f"Duvar {i+1} ve Duvar {j+1} çakışıyor",
                            severity=ErrorSeverity.ERROR.value,
                            location=f"Duvarlar {i+1}, {j+1}",
                            suggestion="Duvar pozisyonlarını düzeltin",
                        )
                    )

        # Door validation
        for i, door in enumerate(layout.doors):
            # Check if door is within wall bounds
            if door.wall_index >= len(layout.walls):
                errors.append(
                    ValidationError(
                        code="INVALID_WALL_INDEX",
                        message=f"Kapı {i+1} geçersiz duvar indeksine sahip: {door.wall_index}",
                        severity=ErrorSeverity.CRITICAL.value,
                        location=f"Kapı {i+1}",
                    )
                )
                continue

            wall = layout.walls[door.wall_index]
            wall_length = self.geometry_utils.distance(wall.start, wall.end)

            if (
                door.position + door.width / 2 > wall_length
                or door.position - door.width / 2 < 0
            ):
                errors.append(
                    ValidationError(
                        code="DOOR_OUTSIDE_WALL",
                        message=f"Kapı {i+1} duvar sınırlarının dışında",
                        severity=ErrorSeverity.ERROR.value,
                        location=f"Kapı {i+1}",
                        suggestion="Kapı pozisyonunu duvar içinde tutun",
                    )
                )

            # Check door width constraints
            if door.width < self.min_door_width or door.width > self.max_door_width:
                severity = (
                    ErrorSeverity.ERROR if door.width < 800 else ErrorSeverity.WARNING
                )
                errors.append(
                    ValidationError(
                        code="DOOR_WIDTH_INVALID",
                        message=f"Kapı {i+1} genişliği uygunsuz: {door.width}mm (800-1200mm arası olmalı)",
                        severity=severity.value,
                        location=f"Kapı {i+1}",
                    )
                )

        # Window validation
        for i, window in enumerate(layout.windows):
            if window.wall_index >= len(layout.walls):
                errors.append(
                    ValidationError(
                        code="INVALID_WALL_INDEX",
                        message=f"Pencere {i+1} geçersiz duvar indeksine sahip: {window.wall_index}",
                        severity=ErrorSeverity.CRITICAL.value,
                        location=f"Pencere {i+1}",
                    )
                )
                continue

            wall = layout.walls[window.wall_index]
            wall_length = self.geometry_utils.distance(wall.start, wall.end)

            if (
                window.position + window.width / 2 > wall_length
                or window.position - window.width / 2 < 0
            ):
                errors.append(
                    ValidationError(
                        code="WINDOW_OUTSIDE_WALL",
                        message=f"Pencere {i+1} duvar sınırlarının dışında",
                        severity=ErrorSeverity.ERROR.value,
                        location=f"Pencere {i+1}",
                    )
                )

            # Check window height and sill height
            if window.sill_height + window.height > wall.height - 100:  # 10cm clearance
                warnings.append(
                    ValidationError(
                        code="WINDOW_HEIGHT_HIGH",
                        message=f"Pencere {i+1} duvar yüksekliğine yakın",
                        severity=ErrorSeverity.WARNING.value,
                        location=f"Pencere {i+1}",
                    )
                )

        return errors, warnings

    async def _validate_spatial_constraints(
        self, layout: LayoutData
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Mekansal kısıtlamalar - oda boyutları, erişilebilirlik"""

        errors = []
        warnings = []

        # Room area validation
        for room in layout.rooms:
            if room.area < self.min_room_area:
                errors.append(
                    ValidationError(
                        code="ROOM_TOO_SMALL",
                        message=f"Oda '{room.name}' çok küçük: {room.area:.1f}m² (minimum {self.min_room_area}m²)",
                        severity=ErrorSeverity.ERROR.value,
                        location=room.name,
                        suggestion=f"Oda alanını minimum {self.min_room_area}m² yapın",
                    )
                )

        # Check for room connectivity
        room_doors = self._find_room_doors(layout)
        for room in layout.rooms:
            if room.name not in room_doors or len(room_doors[room.name]) == 0:
                errors.append(
                    ValidationError(
                        code="ROOM_NO_ACCESS",
                        message=f"Oda '{room.name}' erişilebilir değil (kapı yok)",
                        severity=ErrorSeverity.CRITICAL.value,
                        location=room.name,
                        suggestion="Odaya kapı ekleyin",
                    )
                )

        # Check corridor widths
        corridors = self._extract_corridors(layout)
        for corridor in corridors:
            if corridor["width"] < self.min_corridor_width:
                errors.append(
                    ValidationError(
                        code="CORRIDOR_TOO_NARROW",
                        message=f"Koridor çok dar: {corridor['width']:.0f}mm (minimum {self.min_corridor_width}mm)",
                        severity=ErrorSeverity.ERROR.value,
                        location="Koridor",
                        suggestion=f"Koridor genişliğini minimum {self.min_corridor_width}mm yapın",
                    )
                )

        return errors, warnings

    async def _validate_building_codes(
        self, layout: LayoutData
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Türk Yapı Yönetmeliği uyumluluk kontrolü"""

        errors = []
        warnings = []

        # Delegate to building code validator
        code_result = await self.building_code_validator.validate_layout(layout)

        errors.extend(code_result.get("errors", []))
        warnings.extend(code_result.get("warnings", []))

        return errors, warnings

    async def _validate_safety_requirements(
        self, layout: LayoutData
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Güvenlik gereksinimleri - yangın çıkışı, yapısal güvenlik"""

        errors = []
        warnings = []

        # Fire exit validation
        exterior_doors = [
            door
            for door in layout.doors
            if door.wall_index < len(layout.walls)
            and layout.walls[door.wall_index].type == "exterior"
        ]

        if len(exterior_doors) == 0:
            errors.append(
                ValidationError(
                    code="NO_FIRE_EXIT",
                    message="Yangın çıkışı yok - en az bir dış kapı gerekli",
                    severity=ErrorSeverity.CRITICAL.value,
                    suggestion="Dış duvara kapı ekleyin",
                )
            )

        # Natural light validation
        total_floor_area = sum(room.area for room in layout.rooms)
        total_window_area = sum(
            (window.width * window.height) / 1_000_000  # Convert mm² to m²
            for window in layout.windows
        )

        window_ratio = (
            total_window_area / total_floor_area if total_floor_area > 0 else 0
        )
        if window_ratio < self.min_window_area_ratio:
            warnings.append(
                ValidationError(
                    code="INSUFFICIENT_NATURAL_LIGHT",
                    message=f"Doğal aydınlatma yetersiz: {window_ratio:.3f} (minimum {self.min_window_area_ratio:.3f})",
                    severity=ErrorSeverity.WARNING.value,
                    suggestion="Pencere alanını artırın",
                )
            )

        return errors, warnings

    async def _validate_accessibility(
        self, layout: LayoutData
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Engelli erişim standartları"""

        errors = []
        warnings = []

        # Door width for wheelchair access
        for i, door in enumerate(layout.doors):
            if door.width < 850:  # Minimum for wheelchair
                warnings.append(
                    ValidationError(
                        code="DOOR_WIDTH_ACCESSIBILITY",
                        message=f"Kapı {i+1} engelli erişim için dar: {door.width}mm (minimum 850mm)",
                        severity=ErrorSeverity.WARNING.value,
                        location=f"Kapı {i+1}",
                        suggestion="Kapı genişliğini en az 850mm yapın",
                    )
                )

        # Corridor width for wheelchair access
        corridors = self._extract_corridors(layout)
        for corridor in corridors:
            if corridor["width"] < 1200:  # Minimum for wheelchair turning
                warnings.append(
                    ValidationError(
                        code="CORRIDOR_WIDTH_ACCESSIBILITY",
                        message=f"Koridor engelli erişim için dar: {corridor['width']:.0f}mm (minimum 1200mm)",
                        severity=ErrorSeverity.WARNING.value,
                        suggestion="Koridor genişliğini en az 1200mm yapın",
                    )
                )

        return errors, warnings

    def _determine_validation_status(
        self, errors: List[ValidationError], warnings: List[ValidationError]
    ) -> ValidationStatus:
        """Validation durumunu belirle"""

        critical_errors = [
            e for e in errors if e.severity == ErrorSeverity.CRITICAL.value
        ]
        regular_errors = [e for e in errors if e.severity == ErrorSeverity.ERROR.value]

        if critical_errors:
            return ValidationStatus.REJECTED
        elif len(regular_errors) > 3:  # Too many errors
            return ValidationStatus.REJECTED
        elif regular_errors or warnings:
            return ValidationStatus.REQUIRES_REVIEW
        else:
            return ValidationStatus.REQUIRES_REVIEW  # Always require human review

    def _calculate_confidence_score(
        self,
        layout: LayoutData,
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> float:
        """Güven skorunu hesapla"""

        base_confidence = layout.confidence

        # Reduce confidence based on errors
        critical_penalty = (
            len([e for e in errors if e.severity == ErrorSeverity.CRITICAL.value]) * 0.3
        )
        error_penalty = (
            len([e for e in errors if e.severity == ErrorSeverity.ERROR.value]) * 0.1
        )
        warning_penalty = len(warnings) * 0.05

        adjusted_confidence = max(
            0.0, base_confidence - critical_penalty - error_penalty - warning_penalty
        )

        return round(adjusted_confidence, 3)

    def _calculate_compliance_score(
        self, errors: List[ValidationError], warnings: List[ValidationError]
    ) -> float:
        """Uyumluluk skorunu hesapla"""

        total_issues = len(errors) + len(warnings)
        if total_issues == 0:
            return 1.0

        # Weight by severity
        critical_weight = (
            len([e for e in errors if e.severity == ErrorSeverity.CRITICAL.value]) * 3
        )
        error_weight = (
            len([e for e in errors if e.severity == ErrorSeverity.ERROR.value]) * 2
        )
        warning_weight = len(warnings) * 1

        weighted_issues = critical_weight + error_weight + warning_weight
        max_possible_score = 10  # Assume max 10 weighted issues for full compliance

        score = max(0.0, 1.0 - (weighted_issues / max_possible_score))

        return round(score, 3)

    def _requires_human_review(
        self, status: ValidationStatus, confidence: float, errors: List[ValidationError]
    ) -> bool:
        """İnsan incelemesi gerekli mi"""

        # Always require review for critical errors or low confidence
        if status == ValidationStatus.REJECTED:
            return True
        if confidence < 0.7:
            return True
        if any(e.severity == ErrorSeverity.CRITICAL.value for e in errors):
            return True

        # For now, always require human review for architectural layouts
        return True

    def _find_room_doors(self, layout: LayoutData) -> Dict[str, List[DoorElement]]:
        """Her oda için kapıları bul"""

        room_doors = {}
        for room in layout.rooms:
            room_doors[room.name] = []

        # Simple implementation - assumes room boundaries are wall indices
        for door in layout.doors:
            if door.wall_index < len(layout.walls):
                # Find which room this door belongs to
                # This is simplified - actual implementation would need geometric analysis
                for room in layout.rooms:
                    if door.wall_index in room.boundaries:
                        room_doors[room.name].append(door)
                        break

        return room_doors

    def _extract_corridors(self, layout: LayoutData) -> List[Dict[str, Any]]:
        """Koridorları tespit et ve genişliklerini hesapla"""

        # Simplified corridor detection
        # In real implementation, this would analyze the layout geometry
        corridors = []

        # For now, assume any space between rooms is a corridor
        # This is a placeholder implementation
        for room in layout.rooms:
            if "koridor" in room.name.lower() or "hole" in room.name.lower():
                # Estimate corridor width from area (assuming length is 3x width)
                estimated_width = math.sqrt(room.area * 1000 / 3)  # Convert to mm
                corridors.append(
                    {"name": room.name, "width": estimated_width, "area": room.area}
                )

        # If no corridors found, assume minimum corridor space
        if not corridors:
            corridors.append(
                {
                    "name": "Genel sirkülasyon",
                    "width": 1000,  # Default assumption
                    "area": 5.0,
                }
            )

        return corridors
