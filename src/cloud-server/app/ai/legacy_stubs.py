"""
Legacy AI Client Stubs for ArchBuilder.AI

These are deprecated stub implementations. 
Use the real implementations instead:
- app.ai.openai.client.OpenAIClient  
- app.ai.vertex.client.VertexAIClient
"""

import warnings
from typing import Any, Dict


class OpenAIClient:
    """Legacy OpenAI stub class - gerçek implementasyon openai/client.py'da"""

    def __init__(self):
        warnings.warn(
            "Using legacy OpenAIClient stub. Use app.ai.openai.client.OpenAIClient instead.",
            DeprecationWarning,
            stacklevel=2
        )

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return {
            "provider": "openai-stub", 
            "model": "legacy-stub",
            "output": {"message": "Legacy stub - use real OpenAI client", "input_preview": prompt[:50]}, 
            "metadata": {"is_stub": True, **kwargs}
        }


class VertexClient:
    """Legacy Vertex stub class - gerçek implementasyon vertex/client.py'da"""

    def __init__(self):
        warnings.warn(
            "Using legacy VertexClient stub. Use app.ai.vertex.client.VertexAIClient instead.",
            DeprecationWarning,
            stacklevel=2
        )

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return {
            "provider": "vertex-stub", 
            "model": "legacy-stub",
            "output": {"message": "Legacy stub - use real Vertex AI client", "input_preview": prompt[:50]}, 
            "metadata": {"is_stub": True, **kwargs}
        }