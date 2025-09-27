"""
Gerçek Vertex AI (Google Cloud) entegrasyonu
ArchBuilder.AI için Gemini model entegrasyonu
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold

from app.core.config import settings
from app.ai.interfaces import AIClient

logger = logging.getLogger(__name__)


class VertexAIClient(AIClient):
    """Gerçek Vertex AI client implementasyonu"""
    
    def __init__(self):
        # Vertex AI initialize
        if settings.google_cloud_project and settings.google_cloud_region:
            vertexai.init(
                project=settings.google_cloud_project, 
                location=settings.google_cloud_region
            )
        else:
            logger.warning("Vertex AI credentials eksik, stub mode aktif")
        
        self.project_id = settings.google_cloud_project
        self.location = settings.google_cloud_region
        self.cost_per_1k_input_chars = 0.00025  # Gemini pricing (approximate)
        self.cost_per_1k_output_chars = 0.0005
        
        # Safety settings
        self.safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
        ]
    
    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """AI response üretimi Vertex AI Gemini ile"""
        
        if not self.project_id:
            # Fallback to stub if no credentials
            return await self._generate_stub(prompt, **kwargs)
        
        correlation_id = kwargs.get('correlation_id', f"vertex_{int(time.time())}")
        model_name = kwargs.get('model', 'gemini-1.5-pro')
        
        start_time = time.time()
        
        try:
            # Model oluştur
            model = GenerativeModel(
                model_name=model_name,
                system_instruction=self._create_system_instruction(kwargs.get('task_type', 'general'))
            )
            
            # Generation config
            generation_config = GenerationConfig(
                temperature=kwargs.get('temperature', 0.1),
                top_p=kwargs.get('top_p', 0.8),
                top_k=kwargs.get('top_k', 40),
                max_output_tokens=kwargs.get('max_tokens', 8192),
                response_mime_type="application/json" if kwargs.get('json_mode', True) else "text/plain"
            )
            
            # Log işlem başlangıcı
            logger.info(
                f"Vertex AI çağrısı başladı",
                extra={
                    "correlation_id": correlation_id,
                    "model": model_name,
                    "project": self.project_id,
                    "location": self.location
                }
            )
            
            # Generate content
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
            )
            
            processing_time = time.time() - start_time
            
            # Response işleme
            if not response.candidates:
                raise ValueError("Vertex AI response boş")
            
            candidate = response.candidates[0]
            if candidate.finish_reason.name == "SAFETY":
                raise ValueError("Vertex AI güvenlik filtresine takıldı")
            
            output_content = candidate.content.parts[0].text
            
            # Token/character count estimation
            input_chars = len(prompt)
            output_chars = len(output_content)
            
            # Cost hesaplama (approximate)
            input_cost = (input_chars / 1000) * self.cost_per_1k_input_chars
            output_cost = (output_chars / 1000) * self.cost_per_1k_output_chars
            total_cost = input_cost + output_cost
            
            # JSON parse et (eğer json_mode açık ise)
            if kwargs.get('json_mode', True):
                try:
                    parsed_content = json.loads(output_content)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"JSON parse hatası: {str(e)}",
                        extra={"correlation_id": correlation_id, "content": output_content[:200]}
                    )
                    parsed_content = {"raw_output": output_content, "parse_error": True}
            else:
                parsed_content = {"content": output_content}
            
            # Usage metadata (if available)
            usage_metadata = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage_metadata = {
                    "prompt_token_count": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "candidates_token_count": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_token_count": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            result = {
                "provider": "vertex_ai",
                "model": model_name,
                "output": parsed_content,
                "metadata": {
                    "correlation_id": correlation_id,
                    "processing_time_seconds": processing_time,
                    "input_chars": input_chars,
                    "output_chars": output_chars,
                    "total_cost_usd": round(total_cost, 6),
                    "confidence": self._calculate_confidence(candidate),
                    "finish_reason": candidate.finish_reason.name,
                    "usage_metadata": usage_metadata,
                    "safety_ratings": self._extract_safety_ratings(candidate)
                }
            }
            
            # Başarılı işlem logla
            logger.info(
                f"Vertex AI işlemi tamamlandı",
                extra={
                    "correlation_id": correlation_id,
                    "processing_time": processing_time,
                    "total_cost": total_cost,
                    "output_chars": output_chars
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Hata logla
            logger.error(
                f"Vertex AI hatası: {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "processing_time": processing_time,
                    "error_type": type(e).__name__
                }
            )
            
            # Fallback response
            return {
                "provider": "vertex_ai",
                "model": model_name,
                "output": {"error": True, "message": str(e)},
                "metadata": {
                    "correlation_id": correlation_id,
                    "processing_time_seconds": processing_time,
                    "input_chars": len(prompt),
                    "output_chars": 0,
                    "total_cost_usd": 0.0,
                    "confidence": 0.0,
                    "error": True
                }
            }
    
    async def generate_streaming(self, prompt: str, **kwargs: Any):
        """Streaming response için Vertex AI"""
        
        if not self.project_id:
            yield {"content": "Vertex AI credentials eksik", "error": True}
            return
        
        correlation_id = kwargs.get('correlation_id', f"vertex_stream_{int(time.time())}")
        model_name = kwargs.get('model', 'gemini-1.5-pro')
        
        try:
            model = GenerativeModel(
                model_name=model_name,
                system_instruction=self._create_system_instruction(kwargs.get('task_type', 'general'))
            )
            
            generation_config = GenerationConfig(
                temperature=kwargs.get('temperature', 0.1),
                max_output_tokens=kwargs.get('max_tokens', 8192)
            )
            
            # Stream generate
            response_stream = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    content = chunk.candidates[0].content.parts[0].text
                    yield {
                        "content": content,
                        "correlation_id": correlation_id,
                        "provider": "vertex_ai"
                    }
        
        except Exception as e:
            logger.error(f"Vertex AI streaming hatası: {str(e)}", extra={"correlation_id": correlation_id})
            yield {
                "content": "",
                "error": str(e),
                "correlation_id": correlation_id,
                "provider": "vertex_ai"
            }
    
    def _create_system_instruction(self, task_type: str) -> str:
        """Task tipine göre system instruction oluştur"""
        
        base_instruction = """You are an expert architect and BIM specialist working with ArchBuilder.AI.
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
5. Provide detailed reasoning in Turkish with technical terms in English
6. Prioritize building code compliance and safety"""
        
        if task_type == "layout_generation":
            return base_instruction + """

LAYOUT GENERATION SPECIFIC TASKS:
- Generate precise wall coordinates with start/end points
- Calculate door and window positions as wall offsets  
- Ensure minimum room areas per Turkish standards
- Validate circulation paths and accessibility
- Check fire safety and egress requirements
- Optimize for natural lighting and ventilation"""
            
        elif task_type == "building_code_validation":
            return base_instruction + """

BUILDING CODE VALIDATION TASKS:
- Apply Turkish İmar Yönetmeliği comprehensively
- Check all accessibility requirements (disabled access)
- Validate fire escape routes and maximum distances
- Verify structural requirements and load calculations
- Ensure natural lighting and ventilation standards
- Check parking and green space requirements"""
            
        elif task_type == "document_analysis":
            return base_instruction + """

DOCUMENT ANALYSIS TASKS:
- Extract architectural requirements from Turkish documents
- Identify building specifications and constraints
- Parse regulatory compliance requirements
- Generate structured data from unstructured text
- Preserve original terminology and measurements
- Flag unclear or conflicting information"""
            
        return base_instruction
    
    def _calculate_confidence(self, candidate) -> float:
        """Candidate kalitesine göre confidence hesapla"""
        
        if not candidate or not candidate.content.parts:
            return 0.0
        
        # Finish reason kontrolü
        finish_reason = candidate.finish_reason.name
        if finish_reason == "MAX_TOKENS":
            return 0.6  # Truncated response
        elif finish_reason == "SAFETY":
            return 0.2  # Safety filtered
        elif finish_reason != "STOP":
            return 0.4  # Unknown finish reason
        
        # Content kalitesi
        content = candidate.content.parts[0].text
        if len(content) < 50:
            return 0.5  # Çok kısa response
        
        # Safety ratings kontrolü
        safety_ratings = candidate.safety_ratings
        blocked_ratings = [r for r in safety_ratings if r.probability.name in ["HIGH", "MEDIUM"]]
        if blocked_ratings:
            return 0.6  # Moderate safety concerns
        
        # JSON structure kontrolü
        try:
            json.loads(content)
            return 0.95  # Valid JSON
        except:
            return 0.8  # Invalid JSON ama quality content
    
    def _extract_safety_ratings(self, candidate) -> Dict[str, str]:
        """Safety ratings bilgisini çıkar"""
        
        if not candidate.safety_ratings:
            return {}
        
        ratings = {}
        for rating in candidate.safety_ratings:
            category = rating.category.name
            probability = rating.probability.name
            ratings[category] = probability
        
        return ratings
    
    async def _generate_stub(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Credentials yoksa stub response"""
        
        correlation_id = kwargs.get('correlation_id', f"vertex_stub_{int(time.time())}")
        
        return {
            "provider": "vertex_ai",
            "model": "gemini-stub",
            "output": {
                "message": "Vertex AI stub response - credentials required for real integration",
                "input_preview": prompt[:100],
                "requires_setup": True
            },
            "metadata": {
                "correlation_id": correlation_id,
                "processing_time_seconds": 0.1,
                "input_chars": len(prompt),
                "output_chars": 50,
                "total_cost_usd": 0.0,
                "confidence": 0.5,
                "is_stub": True
            }
        }
    
    async def validate_credentials(self) -> bool:
        """Vertex AI credentials geçerliliğini kontrol et"""
        
        if not self.project_id or not self.location:
            return False
        
        try:
            # Basit bir test çağrısı
            model = GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(
                "Test",
                generation_config=GenerationConfig(max_output_tokens=10)
            )
            return bool(response.candidates)
        except Exception as e:
            logger.error(f"Vertex AI credentials validation hatası: {str(e)}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Model bilgilerini getir"""
        return {
            "provider": "vertex_ai",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            "default_model": "gemini-1.5-pro",
            "max_output_tokens": 8192,
            "supports_json_mode": True,
            "supports_streaming": True,
            "supports_multimodal": True,
            "project_id": self.project_id,
            "location": self.location,
            "cost_per_1k_chars": {
                "input": self.cost_per_1k_input_chars,
                "output": self.cost_per_1k_output_chars
            }
        }


# Convenience functions
async def create_vertex_client() -> VertexAIClient:
    """Vertex AI client instance oluştur"""
    client = VertexAIClient()
    
    # Credentials validation (optional)
    if client.project_id and not await client.validate_credentials():
        logger.warning("Vertex AI credentials geçersiz, stub mode kullanılacak")
    
    return client