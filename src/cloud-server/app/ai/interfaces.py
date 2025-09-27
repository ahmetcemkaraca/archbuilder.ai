"""
AI Client Interfaces for ArchBuilder.AI

This module defines the core protocols and abstract base classes
for AI client implementations across different providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, Optional


class AIClient(Protocol):
    """Protocol defining the interface for AI client implementations."""

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate AI response from a textual prompt."""
        ...

    async def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project data and provide insights."""
        ...


class BaseAIClient(ABC):
    """Abstract base class for AI client implementations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the AI client with configuration."""
        self.config = config or {}

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate AI response from a textual prompt."""
        pass

    @abstractmethod
    async def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project data and provide insights."""
        pass

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the AI model."""
        return {
            "provider": self.__class__.__name__.replace("Client", "").lower(),
            "version": self.config.get("version", "unknown"),
            "model": self.config.get("model", "default")
        }
