from __future__ import annotations

"""
Basic metadata extraction for PDF and generic files.
"""

from pathlib import Path
from typing import Any, Dict


def extract_basic_metadata(path: Path) -> Dict[str, Any]:
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "extension": path.suffix.lower(),
    }
