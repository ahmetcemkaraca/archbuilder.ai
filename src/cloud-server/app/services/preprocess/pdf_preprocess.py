from __future__ import annotations

"""
PDF preprocess interface (stub): extract page count and basic text (optional dependency later).
"""

from pathlib import Path
from typing import Any, Dict


def preprocess_pdf(path: Path) -> Dict[str, Any]:
    # TR: Harici bağımlılık eklemeden sade metaveri döndürür
    return {
        "type": "pdf",
        "pages": None,
        "notes": "Install pdfminer.six or pypdf2 later for content extraction",
    }
