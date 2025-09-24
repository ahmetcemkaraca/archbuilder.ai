"""
AI Interfaces

Bu modül, AI istemcileri ve prompt işleme için ortak arayüzleri tanımlar.
Yorumlar Türkçe, kod ve identifier'lar İngilizce tutulur.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol


@dataclass(frozen=True)
class PromptRenderResult:
    """Rendered prompt result container."""

    prompt_text: str
    metadata: Mapping[str, Any]


class PromptTemplateLoader(Protocol):
    """Loads prompt templates by name and version."""

    def load(self, template_name: str, version: Optional[str] = None) -> str:  # noqa: D401
        ...


class PromptRenderer(Protocol):
    """Renders a template string using a context mapping."""

    def render(self, template_text: str, context: Mapping[str, Any]) -> PromptRenderResult:  # noqa: D401
        ...


class AIClient(Protocol):
    """Minimal AI client interface."""

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:  # noqa: D401
        ...

