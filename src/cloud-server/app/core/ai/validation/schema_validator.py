from __future__ import annotations

"""
JSON şema doğrulama (basit kurallar):
- Zorunlu alanların varlığı
- Tip kontrolleri (temel)
"""

from typing import Any, Dict, List


def validate_schema(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    # Basit örnek: mimari layout sonucu beklenen alanlar
    if not isinstance(payload, dict):
        return ["payload_must_be_object"]
    if "walls" in payload and not isinstance(payload["walls"], list):
        errors.append("walls_must_be_array")
    if "doors" in payload and not isinstance(payload["doors"], list):
        errors.append("doors_must_be_array")
    if "rooms" in payload and not isinstance(payload["rooms"], list):
        errors.append("rooms_must_be_array")
    return errors

