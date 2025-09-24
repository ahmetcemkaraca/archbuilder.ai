from __future__ import annotations

"""
Bina yönetmeliği kontrolleri (temel):
- Konut için koridor genişliği min 1200mm
"""

from typing import Any, Dict, List


def validate_building_code(payload: Dict[str, Any], building_type: str = "residential") -> List[str]:
    errors: List[str] = []
    if building_type == "residential":
        corridors = payload.get("corridors", [])
        for idx, c in enumerate(corridors):
            width = float(c.get("width", 0))
            if width < 1200:
                errors.append(f"corridor_{idx}_below_min_width")
    return errors

