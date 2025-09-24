from __future__ import annotations

from typing import Dict


class ModelSelector:
    """Basit kural tabanlı model seçici."""

    def select(self, language: str, complexity: str = "simple") -> Dict[str, str]:
        lang = (language or "").lower()
        if lang == "tr" and complexity != "high":
            return {"provider": "vertex", "model": "gemini-2.5-flash-lite"}
        if complexity == "high":
            return {"provider": "openai", "model": "gpt-4.1"}
        return {"provider": "openai", "model": "gpt-4.1"}


