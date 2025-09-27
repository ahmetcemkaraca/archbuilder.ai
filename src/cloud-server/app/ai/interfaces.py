from __future__ import annotations

from typing import Any, Dict, Protocol


class AIClient(Protocol):
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate AI response from a textual prompt."""
        ...


class OpenAIClient:
    """Basit OpenAI stub (gerçek anahtar/çağrı yok)."""

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return {"model": "openai-stub", "output": prompt[:50], "meta": kwargs}


class VertexClient:
    """Basit Vertex stub (gerçek çağrı yok)."""

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return {"model": "vertex-stub", "output": prompt[:50], "meta": kwargs}
