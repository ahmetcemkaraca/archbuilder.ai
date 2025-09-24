from __future__ import annotations

"""
Geometrik kontroller:
- Duvar uzunluğu minimum eşik
- Kapı genişliği makul aralık
"""

from typing import Any, Dict, List


def _wall_length_ok(wall: Dict[str, Any]) -> bool:
    try:
        sp, ep = wall["start"], wall["end"]
        dx, dy = float(ep["x"]) - float(sp["x"]), float(ep["y"]) - float(sp["y"])
        length = (dx * dx + dy * dy) ** 0.5
        return length >= 100.0
    except Exception:
        return False


def validate_geometry(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    walls = payload.get("walls", [])
    for idx, wall in enumerate(walls):
        if not _wall_length_ok(wall):
            errors.append(f"wall_{idx}_too_short")
    doors = payload.get("doors", [])
    for idx, door in enumerate(doors):
        width = float(door.get("width", 0))
        if width < 600 or width > 2000:
            errors.append(f"door_{idx}_width_out_of_range")
    return errors

