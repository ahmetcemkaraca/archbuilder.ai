from __future__ import annotations

"""
CAD preprocess interface (stub) for DXF/IFC metadata.
"""

from pathlib import Path
from typing import Any, Dict


def preprocess_cad(path: Path) -> Dict[str, Any]:
    # TR: Harici CAD lib yok; yalın metadata
    return {
        "type": "cad",
        "format": path.suffix.lower().lstrip('.'),
        "notes": "Integrate ifcopenshell or ezdxf for detailed parsing later",
    }
