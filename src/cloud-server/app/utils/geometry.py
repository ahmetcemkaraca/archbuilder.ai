"""
Geometry Utilities for ArchBuilder.AI

Provides geometric calculations and validations for architectural layouts.
Includes 2D geometry operations, collision detection, and spatial analysis.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import math
from typing import Tuple, List, Optional
import numpy as np

from ..schemas.layout_schemas import Point2D


class GeometryUtils:
    """
    2D geometrik hesaplamalar ve validasyon yardımcı sınıfı

    Bu sınıf şu işlevleri sağlar:
    - Nokta ve çizgi hesaplamaları
    - Çakışma tespiti
    - Alan ve mesafe hesaplamaları
    - Geometrik validasyonlar
    """

    def distance(self, point1: Point2D, point2: Point2D) -> float:
        """İki nokta arası mesafe (mm)"""
        dx = point2.x - point1.x
        dy = point2.y - point1.y
        return math.sqrt(dx * dx + dy * dy)

    def line_length(self, start: Point2D, end: Point2D) -> float:
        """Çizgi uzunluğu (mm)"""
        return self.distance(start, end)

    def lines_overlap(
        self,
        line1: Tuple[Point2D, Point2D],
        line2: Tuple[Point2D, Point2D],
        tolerance: float = 10.0,  # mm
    ) -> bool:
        """
        İki çizgi çakışıyor mu kontrol et

        Args:
            line1: İlk çizgi (başlangıç, bitiş)
            line2: İkinci çizgi (başlangıç, bitiş)
            tolerance: Tolerans mesafesi (mm)

        Returns:
            bool: Çakışma var mı
        """

        # Convert to numpy arrays for easier calculation
        p1_start = np.array([line1[0].x, line1[0].y])
        p1_end = np.array([line1[1].x, line1[1].y])
        p2_start = np.array([line2[0].x, line2[0].y])
        p2_end = np.array([line2[1].x, line2[1].y])

        # Check if lines are parallel
        v1 = p1_end - p1_start
        v2 = p2_end - p2_start

        # Normalize vectors
        len1 = np.linalg.norm(v1)
        len2 = np.linalg.norm(v2)

        if len1 == 0 or len2 == 0:
            return False

        v1_norm = v1 / len1
        v2_norm = v2 / len2

        # Check if lines are parallel (cross product near zero)
        cross_product = abs(np.cross(v1_norm, v2_norm))

        if cross_product < 0.01:  # Nearly parallel
            # Check if lines are collinear and overlapping
            # Distance from p2_start to line1
            dist_to_line = self._point_to_line_distance(
                Point2D(x=p2_start[0], y=p2_start[1]), line1[0], line1[1]
            )

            if dist_to_line <= tolerance:
                # Check if any part of line2 overlaps with line1
                return self._line_segments_overlap(
                    p1_start, p1_end, p2_start, p2_end, tolerance
                )

        # Check if lines intersect
        intersection = self._line_intersection(p1_start, p1_end, p2_start, p2_end)
        if intersection is not None:
            # Check if intersection is within both line segments
            if self._point_on_line_segment(
                intersection, p1_start, p1_end, tolerance
            ) and self._point_on_line_segment(
                intersection, p2_start, p2_end, tolerance
            ):
                return True

        return False

    def _point_to_line_distance(
        self, point: Point2D, line_start: Point2D, line_end: Point2D
    ) -> float:
        """Nokta ile çizgi arası minimum mesafe"""

        # Convert to numpy arrays
        p = np.array([point.x, point.y])
        a = np.array([line_start.x, line_start.y])
        b = np.array([line_end.x, line_end.y])

        # Line vector
        ab = b - a

        # Vector from line start to point
        ap = p - a

        # Project point onto line
        ab_length_squared = np.dot(ab, ab)

        if ab_length_squared == 0:
            # Line has zero length, return distance to start point
            return np.linalg.norm(ap)

        # Parameter t for projection
        t = np.dot(ap, ab) / ab_length_squared

        # Clamp t to line segment
        t = max(0.0, min(1.0, t))

        # Find closest point on line segment
        closest_point = a + t * ab

        # Return distance
        return np.linalg.norm(p - closest_point)

    def _line_segments_overlap(
        self,
        p1_start: np.ndarray,
        p1_end: np.ndarray,
        p2_start: np.ndarray,
        p2_end: np.ndarray,
        tolerance: float,
    ) -> bool:
        """İki çizgi parçası çakışıyor mu (collinear durumda)"""

        # Project all points onto the first line direction
        line1_vec = p1_end - p1_start
        line1_length = np.linalg.norm(line1_vec)

        if line1_length == 0:
            return False

        line1_unit = line1_vec / line1_length

        # Project points onto line1 direction
        t1_start = 0.0
        t1_end = line1_length
        t2_start = np.dot(p2_start - p1_start, line1_unit)
        t2_end = np.dot(p2_end - p1_start, line1_unit)

        # Ensure t2_start <= t2_end
        if t2_start > t2_end:
            t2_start, t2_end = t2_end, t2_start

        # Check overlap
        return not (t1_end < t2_start - tolerance or t2_end < t1_start - tolerance)

    def _line_intersection(
        self,
        p1_start: np.ndarray,
        p1_end: np.ndarray,
        p2_start: np.ndarray,
        p2_end: np.ndarray,
    ) -> Optional[np.ndarray]:
        """İki çizginin kesişim noktası (sonsuz çizgiler için)"""

        x1, y1 = p1_start
        x2, y2 = p1_end
        x3, y3 = p2_start
        x4, y4 = p2_end

        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if abs(denominator) < 1e-10:
            # Lines are parallel
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator

        # Calculate intersection point
        intersection_x = x1 + t * (x2 - x1)
        intersection_y = y1 + t * (y2 - y1)

        return np.array([intersection_x, intersection_y])

    def _point_on_line_segment(
        self,
        point: np.ndarray,
        line_start: np.ndarray,
        line_end: np.ndarray,
        tolerance: float,
    ) -> bool:
        """Nokta çizgi parçası üzerinde mi"""

        # Check if point is within bounding box of line segment
        min_x = min(line_start[0], line_end[0]) - tolerance
        max_x = max(line_start[0], line_end[0]) + tolerance
        min_y = min(line_start[1], line_end[1]) - tolerance
        max_y = max(line_start[1], line_end[1]) + tolerance

        return min_x <= point[0] <= max_x and min_y <= point[1] <= max_y

    def polygon_area(self, vertices: List[Point2D]) -> float:
        """
        Poligon alanı (shoelace formula)

        Args:
            vertices: Poligon köşe noktaları (saat yönü veya tersine)

        Returns:
            float: Alan (mm²)
        """

        if len(vertices) < 3:
            return 0.0

        area = 0.0
        n = len(vertices)

        for i in range(n):
            j = (i + 1) % n
            area += vertices[i].x * vertices[j].y
            area -= vertices[j].x * vertices[i].y

        return abs(area) / 2.0

    def point_in_polygon(self, point: Point2D, vertices: List[Point2D]) -> bool:
        """
        Nokta poligon içinde mi (ray casting algorithm)

        Args:
            point: Test edilecek nokta
            vertices: Poligon köşeleri

        Returns:
            bool: Nokta içerde mi
        """

        x, y = point.x, point.y
        n = len(vertices)
        inside = False

        p1x, p1y = vertices[0].x, vertices[0].y
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n].x, vertices[i % n].y

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def bounding_box(self, points: List[Point2D]) -> Tuple[Point2D, Point2D]:
        """
        Noktalar için bounding box

        Args:
            points: Nokta listesi

        Returns:
            Tuple[Point2D, Point2D]: (min_point, max_point)
        """

        if not points:
            return Point2D(x=0, y=0), Point2D(x=0, y=0)

        min_x = min(p.x for p in points)
        min_y = min(p.y for p in points)
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)

        return Point2D(x=min_x, y=min_y), Point2D(x=max_x, y=max_y)

    def rectangle_area(self, width: float, height: float) -> float:
        """Dikdörtgen alan (mm²)"""
        return width * height

    def circle_area(self, radius: float) -> float:
        """Daire alan (mm²)"""
        return math.pi * radius * radius

    def angle_between_vectors(
        self, v1: Tuple[float, float], v2: Tuple[float, float]
    ) -> float:
        """
        İki vektör arası açı (radyan)

        Args:
            v1: İlk vektör (dx, dy)
            v2: İkinci vektör (dx, dy)

        Returns:
            float: Açı (0 to π radyan)
        """

        # Normalize vectors
        len1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
        len2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])

        if len1 == 0 or len2 == 0:
            return 0.0

        unit1 = (v1[0] / len1, v1[1] / len1)
        unit2 = (v2[0] / len2, v2[1] / len2)

        # Dot product
        dot_product = unit1[0] * unit2[0] + unit1[1] * unit2[1]

        # Clamp to avoid numerical errors
        dot_product = max(-1.0, min(1.0, dot_product))

        return math.acos(dot_product)

    def is_rectangle_valid(
        self, corners: List[Point2D], tolerance: float = 10.0
    ) -> bool:
        """
        Dikdörtgen geçerli mi kontrol et

        Args:
            corners: 4 köşe noktası (sıralı)
            tolerance: Açı toleransı (mm)

        Returns:
            bool: Geçerli dikdörtgen mi
        """

        if len(corners) != 4:
            return False

        # Check if all angles are approximately 90 degrees
        for i in range(4):
            p1 = corners[i]
            p2 = corners[(i + 1) % 4]
            p3 = corners[(i + 2) % 4]

            # Vectors from p2
            v1 = (p1.x - p2.x, p1.y - p2.y)
            v2 = (p3.x - p2.x, p3.y - p2.y)

            angle = self.angle_between_vectors(v1, v2)
            angle_degrees = math.degrees(angle)

            # Should be approximately 90 degrees
            if abs(angle_degrees - 90.0) > tolerance:
                return False

        return True

    def centroid(self, points: List[Point2D]) -> Point2D:
        """Noktaların merkezi (centroid)"""

        if not points:
            return Point2D(x=0, y=0)

        total_x = sum(p.x for p in points)
        total_y = sum(p.y for p in points)
        count = len(points)

        return Point2D(x=total_x / count, y=total_y / count)
