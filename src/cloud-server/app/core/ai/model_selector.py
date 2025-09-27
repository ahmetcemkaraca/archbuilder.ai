"""
Model Selector

Basit kural tabanlı model seçim mantığı. Sağlayıcı adları doğru ve açık yazılır:
- OpenAI (or Azure OpenAI)
- Vertex AI (Google)
- Anthropic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelChoice:
    provider: str
    model: str


def select_model(
    task: str, latency_sensitive: bool = False, prefer_local: bool = False
) -> ModelChoice:
    """Select model by task category.

    Kurallar (örnek):
    - validation → Vertex AI text-bison veya latest text model
    - layout_generation → OpenAI GPT-4o-mini benzeri hızlı model
    - fallback → Anthropic Claude 3 Haiku
    """

    normalized = task.strip().lower()
    if normalized in {"validation", "code_validation", "schema_validation"}:
        return ModelChoice(provider="Vertex AI", model="text-bison-001")

    if normalized in {"layout_generation", "design", "draft"}:
        if latency_sensitive:
            return ModelChoice(provider="OpenAI", model="gpt-4o-mini")
        return ModelChoice(provider="OpenAI", model="gpt-4o")

    if prefer_local:
        return ModelChoice(provider="Local", model="llama3.1-8b-instruct-q4")

    return ModelChoice(provider="Anthropic", model="claude-3-haiku-20240307")
