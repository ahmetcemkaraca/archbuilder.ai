"""
AI Client interfaces ve abstract classes
ArchBuilder.AI AI entegrasyonu için standart protokoller
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, AsyncGenerator, Optional


class AIClient(Protocol):
    """AI Client protokolü - tüm AI client'lar bu interface'i implement etmeli"""
    
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        AI response üretimi
        
        Args:
            prompt: Input prompt text
            **kwargs: Model-specific parameters
            
        Returns:
            Dict containing model response and metadata
        """
        raise NotImplementedError("Subclasses must implement generate method")
    
    async def generate_streaming(self, prompt: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming AI response üretimi
        
        Args:
            prompt: Input prompt text  
            **kwargs: Model-specific parameters
            
        Yields:
            Dict chunks of streaming response
        """
        raise NotImplementedError("Subclasses must implement generate_streaming method")
    
    async def validate_credentials(self) -> bool:
        """API credentials geçerliliğini kontrol et"""
        raise NotImplementedError("Subclasses must implement validate_credentials method")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Model bilgileri ve capabilities"""
        raise NotImplementedError("Subclasses must implement get_model_info method")


class BaseAIClient(ABC):
    """Abstract base class for AI clients with common functionality"""
    
    def __init__(self):
        self.provider_name = "unknown"
        self.default_model = "unknown"
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate AI response - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate method")
    
    @abstractmethod
    async def generate_streaming(self, prompt: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_streaming method")
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate API credentials - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement validate_credentials method")
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_model_info method")
    
    def _create_standard_response(
        self, 
        output: Any, 
        metadata: Dict[str, Any],
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Standard response formatı oluştur"""
        
        return {
            "provider": self.provider_name,
            "model": metadata.get("model", self.default_model),
            "output": output,
            "metadata": {
                **metadata,
                "error": bool(error),
                "error_message": error
            }
        }


# Legacy stub classes for backward compatibility
class OpenAIClient:
    """Legacy OpenAI stub class - gerçek implementasyon openai/client.py'da"""
    
    def __init__(self):
        import warnings
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
        import warnings
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


