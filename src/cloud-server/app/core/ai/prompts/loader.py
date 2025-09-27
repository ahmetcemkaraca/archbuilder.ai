from __future__ import annotations

"""
Prompt template loader.

Basit dosya sistemi tabanlı yükleyici; `templates/` altından isim+versiyon ile okur.
"""

from pathlib import Path
from typing import Optional

from ..interfaces import PromptTemplateLoader


class FileSystemPromptTemplateLoader(PromptTemplateLoader):
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or Path(__file__).parent / "templates"

    def load(self, template_name: str, version: Optional[str] = None) -> str:
        safe_name = template_name.strip().lower().replace(" ", "_")
        candidate_files = []
        if version:
            candidate_files.append(self.base_dir / f"{safe_name}_{version}.md")
        candidate_files.append(self.base_dir / f"{safe_name}.md")

        for path in candidate_files:
            if path.exists():
                return path.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"Prompt template not found for '{template_name}' (version={version})"
        )
