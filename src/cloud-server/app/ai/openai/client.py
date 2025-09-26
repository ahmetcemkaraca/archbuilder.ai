"""
Gerçek OpenAI API entegrasyonu
ArchBuilder.AI için GPT-4.1 model entegrasyonu
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
import tiktoken
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings
from app.ai.interfaces import AIClient

logger = logging.getLogger(__name__)


class OpenAIClient(AIClient):
    """Gerçek OpenAI API client implementasyonu"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=httpx.Timeout(60.0, read=30.0, write=10.0, connect=5.0),
            max_retries=3
        )
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.max_tokens = 128000
        self.cost_per_1k_input_tokens = 0.03  # GPT-4 pricing
        self.cost_per_1k_output_tokens = 0.06
    
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """AI response üretimi OpenAI GPT-4.1 ile"""
        
        # Correlation ID oluştur
        correlation_id = kwargs.get('correlation_id', f"openai_{int(time.time())}")
        
        # Token sayısını kontrol et
        input_tokens = len(self.encoding.encode(prompt))
        if input_tokens > self.max_tokens - 1000:  # Output için yer bırak
            raise ValueError(f"Prompt çok uzun: {input_tokens} tokens (max: {self.max_tokens-1000})")
        
        # Request parameters
        model = kwargs.get('model', 'gpt-4-1106-preview')  # GPT-4.1
        temperature = kwargs.get('temperature', 0.1)
        max_output_tokens = kwargs.get('max_tokens', 4000)
        
        # System prompt oluştur
        system_prompt = self._create_system_prompt(kwargs.get('task_type', 'general'))
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        start_time = time.time()
        
        try:
            # Log işlem başlangıcı
            logger.info(
                f"OpenAI API çağrısı başladı",
                extra={
                    "correlation_id": correlation_id,
                    "model": model,
                    "input_tokens": input_tokens,
                    "temperature": temperature
                }
            )
            
            # OpenAI API çağrısı
            response: ChatCompletion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output_tokens,
                response_format={"type": "json_object"} if kwargs.get('json_mode', True) else None
            )
            
            processing_time = time.time() - start_time
            
            # Response işleme
            output_content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            # Cost hesaplama
            input_cost = (input_tokens / 1000) * self.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * self.cost_per_1k_output_tokens
            total_cost = input_cost + output_cost
            
            # JSON parse et (eğer json_mode açık ise)
            if kwargs.get('json_mode', True):
                try:
                    parsed_content = json.loads(output_content)
                except json.JSONDecodeError:
                    logger.warning(
                        f"JSON parse hatası, raw content döndürülüyor",
                        extra={"correlation_id": correlation_id}
                    )
                    parsed_content = {"raw_output": output_content, "parse_error": True}
            else:
                parsed_content = {"content": output_content}
            
            result = {
                "provider": "openai",
                "model": model,
                "output": parsed_content,
                "metadata": {
                    "correlation_id": correlation_id,
                    "processing_time_seconds": processing_time,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_cost_usd": round(total_cost, 4),
                    "confidence": self._calculate_confidence(response),
                    "finish_reason": response.choices[0].finish_reason
                }
            }
            
            # Başarılı işlem logla
            logger.info(
                f"OpenAI işlemi tamamlandı",
                extra={
                    "correlation_id": correlation_id,
                    "processing_time": processing_time,
                    "total_cost": total_cost,
                    "output_tokens": output_tokens
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Hata logla
            logger.error(
                f"OpenAI API hatası: {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "processing_time": processing_time,
                    "error_type": type(e).__name__
                }
            )
            
            # Fallback response
            return {
                "provider": "openai",
                "model": model,
                "output": {"error": True, "message": str(e)},
                "metadata": {
                    "correlation_id": correlation_id,
                    "processing_time_seconds": processing_time,
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "confidence": 0.0,
                    "error": True
                }
            }
    
    async def generate_streaming(self, prompt: str, **kwargs: Any):
        """Streaming response için OpenAI API"""
        
        correlation_id = kwargs.get('correlation_id', f"openai_stream_{int(time.time())}")
        model = kwargs.get('model', 'gpt-4-1106-preview')
        
        messages = [
            {"role": "system", "content": self._create_system_prompt(kwargs.get('task_type', 'general'))},
            {"role": "user", "content": prompt}
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4000),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "correlation_id": correlation_id,
                        "provider": "openai"
                    }
        
        except Exception as e:
            logger.error(f"OpenAI streaming hatası: {str(e)}", extra={"correlation_id": correlation_id})
            yield {
                "content": "",
                "error": str(e),
                "correlation_id": correlation_id,
                "provider": "openai"
            }
    
    def _create_system_prompt(self, task_type: str) -> str:
        """Task tipine göre system prompt oluştur"""
        
        base_prompt = """You are an expert architect and BIM specialist working with ArchBuilder.AI. 
You have deep knowledge of:
- Autodesk Revit API and BIM workflows
- Architectural design principles and building codes
- Turkish building regulations (İmar Yönetmeliği)
- Multi-format CAD processing (DWG, DXF, IFC, RVT)
- Geometric validation and spatial analysis

CRITICAL REQUIREMENTS:
1. ALWAYS respond with valid JSON matching the requested schema
2. ALL coordinates must be in millimeters for Revit compatibility
3. Include confidence scores (0.0-1.0) for all outputs
4. Flag uncertainties with requiresHumanReview: true
5. Provide detailed reasoning in Turkish with technical terms in English"""
        
        if task_type == "layout_generation":
            return base_prompt + """

LAYOUT GENERATION SPECIFIC:
- Generate precise wall coordinates with start/end points
- Calculate door and window positions as wall offsets
- Ensure minimum room areas (5m² residential, 9m² bedroom)
- Validate circulation paths and accessibility
- Check building code compliance for Turkey"""
            
        elif task_type == "building_code_validation":
            return base_prompt + """

BUILDING CODE VALIDATION SPECIFIC:
- Apply Turkish İmar Yönetmeliği standards
- Check accessibility requirements (900mm doors, ramps)
- Validate fire escape routes and distances
- Verify natural lighting ratios (1/8 floor area)
- Ensure structural and spatial compliance"""
            
        elif task_type == "existing_project_analysis":
            return base_prompt + """

EXISTING PROJECT ANALYSIS SPECIFIC:
- Analyze BIM model performance and organization
- Identify compliance issues and improvement opportunities
- Suggest workflow optimizations and standard adherence
- Provide cost-effective enhancement recommendations
- Focus on Revit best practices and family optimization"""
            
        return base_prompt
    
    def _calculate_confidence(self, response: ChatCompletion) -> float:
        """Response kalitesine göre confidence hesapla"""
        
        if not response.choices or not response.choices[0].message.content:
            return 0.0
        
        # Finish reason kontrolü
        if response.choices[0].finish_reason == "length":
            return 0.6  # Truncated response
        elif response.choices[0].finish_reason == "content_filter":
            return 0.3  # Filtered content
        elif response.choices[0].finish_reason != "stop":
            return 0.5  # Unknown finish reason
        
        # Content uzunluğu ve yapısına göre
        content = response.choices[0].message.content
        if len(content) < 50:
            return 0.4  # Çok kısa response
        
        # JSON structure kontrolü
        try:
            json.loads(content)
            return 0.9  # Valid JSON
        except:
            return 0.7  # Invalid JSON ama content var
    
    async def validate_api_key(self) -> bool:
        """API key geçerliliğini kontrol et"""
        try:
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI API key validation hatası: {str(e)}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Model bilgilerini getir"""
        return {
            "provider": "openai",
            "models": ["gpt-4-1106-preview", "gpt-4", "gpt-3.5-turbo-16k"],
            "default_model": "gpt-4-1106-preview",
            "max_tokens": self.max_tokens,
            "supports_json_mode": True,
            "supports_streaming": True,
            "cost_per_1k_tokens": {
                "input": self.cost_per_1k_input_tokens,
                "output": self.cost_per_1k_output_tokens
            }
        }


# Convenience functions
async def create_openai_client() -> OpenAIClient:
    """OpenAI client instance oluştur"""
    client = OpenAIClient()
    
    # API key validation
    if not await client.validate_api_key():
        raise ValueError("Geçersiz OpenAI API key")
    
    return client