"""
Gelişmiş AI Service 
ArchBuilder.AI için gerçek AI entegrasyonu ve işlem yönetimi
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional, List, Union, AsyncGenerator
from uuid import uuid4
from datetime import datetime

from app.database.session import AsyncSession
from app.ai.model_selector import AdvancedModelSelector, TaskComplexity, AnalysisType
from app.ai.prompts.templates.prompt_versioning import registry as prompt_registry
from app.ai.openai.client import create_openai_client
from app.ai.vertex.client import create_vertex_client
from app.database.models.ai_command import AICommand

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Gelişmiş AI service gerçek model entegrasyonu ile"""
    
    def __init__(self) -> None:
        self._selector = AdvancedModelSelector()
        self._openai_client = None
        self._vertex_client = None
        self._client_cache = {}
        
    async def _get_openai_client(self):
        """OpenAI client lazy initialization"""
        if self._openai_client is None:
            try:
                self._openai_client = await create_openai_client()
            except Exception as e:
                logger.error(f"OpenAI client oluşturulamadı: {str(e)}")
                self._openai_client = None
        return self._openai_client
    
    async def _get_vertex_client(self):
        """Vertex AI client lazy initialization"""
        if self._vertex_client is None:
            try:
                self._vertex_client = await create_vertex_client()
            except Exception as e:
                logger.error(f"Vertex AI client oluşturulamadı: {str(e)}")
                self._vertex_client = None
        return self._vertex_client
    
    async def _get_ai_client(self, provider: str):
        """Provider'a göre AI client getir"""
        if provider == "openai":
            return await self._get_openai_client()
        elif provider == "vertex_ai":
            return await self._get_vertex_client()
        else:
            raise ValueError(f"Desteklenmeyen AI provider: {provider}")
    
    async def create_command(
        self,
        db: AsyncSession,
        command: str,
        input_data: Dict[str, Any],
        user_id: Optional[str],
        project_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Gelişmiş AI command oluşturma
        Gerçek AI model entegrasyonu ile
        """
        
        correlation_id = f"ai_cmd_{int(time.time())}_{uuid4().hex[:8]}"
        
        # Input verilerini parse et
        language = input_data.get("language", "en")
        complexity_str = input_data.get("complexity", "simple")
        analysis_type_str = input_data.get("analysis_type", "creation")
        file_format = input_data.get("file_format")
        estimated_tokens = input_data.get("estimated_tokens", 2000)
        region = input_data.get("region", "eu")
        
        # Enum'lara çevir
        try:
            complexity = TaskComplexity(complexity_str)
        except ValueError:
            complexity = TaskComplexity.SIMPLE
            
        try:
            analysis_type = AnalysisType(analysis_type_str)
        except ValueError:
            analysis_type = AnalysisType.CREATION
        
        # Optimum model seçimi
        model_selection = self._selector.select_optimal_model(
            language=language,
            complexity=complexity,
            analysis_type=analysis_type,
            file_format=file_format,
            estimated_tokens=estimated_tokens,
            region=region
        )
        
        logger.info(
            f"Model seçimi tamamlandı",
            extra={
                "correlation_id": correlation_id,
                "selected_model": model_selection["model"],
                "provider": model_selection["provider"],
                "confidence": model_selection["confidence"]
            }
        )
        
        # Prompt oluşturma
        prompt = await self._create_prompt(command, input_data, analysis_type)
        
        # AI command DB'ye kaydet
        ai_command = AICommand(
            id=str(uuid4()),
            user_id=user_id,
            project_id=project_id,
            command=command,
            input={
                **input_data,
                "correlation_id": correlation_id,
                "selected_model": model_selection
            },
            output={
                "status": "created",
                "model_selection": model_selection,
                "prompt_preview": prompt[:200] if prompt else None
            },
        )
        
        db.add(ai_command)
        await db.flush()
        
        # Asynchronous AI processing başlat
        asyncio.create_task(
            self._process_ai_command_async(ai_command.id, prompt, model_selection, correlation_id)
        )
        
        return {
            "id": ai_command.id,
            "correlation_id": correlation_id,
            "created_at": ai_command.created_at.isoformat(),
            "selected_model": model_selection,
            "status": "processing",
            "estimated_cost_usd": model_selection.get("estimated_cost_usd", 0.0)
        }
    
    async def _process_ai_command_async(
        self, 
        command_id: str, 
        prompt: str, 
        model_selection: Dict[str, Any],
        correlation_id: str
    ):
        """Asynchronous AI işleme"""
        
        try:
            # AI client getir
            client = await self._get_ai_client(model_selection["provider"])
            if not client:
                raise ValueError(f"AI client kullanılamıyor: {model_selection['provider']}")
            
            # AI response üret
            response = await client.generate(
                prompt=prompt,
                model=model_selection["model"],
                correlation_id=correlation_id,
                temperature=0.1,
                json_mode=True
            )
            
            # DB'de sonucu güncelle
            await self._update_command_result(command_id, response, "completed")
            
        except Exception as e:
            logger.error(
                f"AI command işleme hatası: {str(e)}",
                extra={"command_id": command_id, "correlation_id": correlation_id}
            )
            
            # Hata durumunda DB güncelle
            error_response = {
                "error": True,
                "message": str(e),
                "correlation_id": correlation_id
            }
            await self._update_command_result(command_id, error_response, "failed")
    
    async def _update_command_result(self, command_id: str, result: Dict[str, Any], status: str):
        """AI command sonucunu DB'de güncelle"""
        # Note: Bu fonksiyon DB session ihtiyacı var, 
        # Production'da dependency injection ile çözülmeli
        pass  # Placeholder for now
    
    async def _create_prompt(
        self, 
        command: str, 
        input_data: Dict[str, Any], 
        analysis_type: AnalysisType
    ) -> str:
        """Command ve input'a göre prompt oluştur"""
        
        try:
            if analysis_type == AnalysisType.CREATION:
                template = prompt_registry.get("layout_generation")
                return template.format(
                    building_type=input_data.get("building_type", "residential"),
                    total_area_m2=input_data.get("total_area_m2", 50),
                    rooms=",".join(input_data.get("rooms", [])) if isinstance(input_data.get("rooms"), list) else str(input_data.get("rooms", "")),
                    style_preference=input_data.get("style_preference", "modern"),
                    accessibility_required=input_data.get("accessibility_required", True)
                )
            
            elif analysis_type == AnalysisType.VALIDATION:
                template = prompt_registry.get("validation_prompt")
                return template.format(
                    layout_data=input_data.get("layout_data", {}),
                    building_codes=input_data.get("building_codes", "Turkish")
                )
            
            elif analysis_type == AnalysisType.EXISTING_PROJECT_ANALYSIS:
                return f"""
                Mevcut proje analizi yapın:
                
                Proje Bilgileri: {input_data}
                
                Lütfen şu konularda analiz yapın:
                1. BIM model optimizasyonu
                2. Tasarım iyileştirmeleri 
                3. Teknik geliştirmeler
                4. İş akışı optimizasyonu
                
                Türkçe açıklamalar ile JSON formatında yanıtlayın.
                """
            
            else:
                return f"Command: {command}\nInput Data: {input_data}"
                
        except Exception as e:
            logger.warning(f"Prompt oluşturma hatası: {str(e)}")
            return f"Command: {command}\nInput Data: {input_data}"
    
    async def get_command(self, db: AsyncSession, id_: str) -> Dict[str, Any] | None:
        """AI command bilgilerini getir"""
        
        result = await db.get(AICommand, id_)
        if not result:
            return None
        
        return {
            "id": result.id,
            "user_id": result.user_id,
            "project_id": result.project_id,
            "command": result.command,
            "input": result.input,
            "output": result.output,
            "created_at": result.created_at.isoformat(),
            "updated_at": getattr(result, 'updated_at', None).isoformat() if getattr(result, 'updated_at', None) is not None else None,
            "status": result.output.get("status", "unknown") if result.output else "unknown",
            "correlation_id": result.input.get("correlation_id") if result.input else None
        }
    
    async def get_commands_by_user(
        self, 
        db: AsyncSession, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Kullanıcının AI command'larını listele"""
        
        # Note: Bu query implementation SQLAlchemy ile yapılacak
        # Placeholder return
        return []
    
    async def generate_streaming_response(
        self,
        command: str,
        input_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming AI response"""
        
        if not correlation_id:
            correlation_id = f"stream_{int(time.time())}_{uuid4().hex[:8]}"
        
        # Model selection
        model_selection = self._selector.select_optimal_model(
            language=input_data.get("language", "en"),
            complexity=TaskComplexity(input_data.get("complexity", "simple")),
            analysis_type=AnalysisType(input_data.get("analysis_type", "creation"))
        )
        
        # Client getir
        client = await self._get_ai_client(model_selection["provider"])
        if not client:
            yield {"error": f"AI client kullanılamıyor: {model_selection['provider']}"}
            return
        
        # Prompt oluştur
        prompt = await self._create_prompt(
            command, 
            input_data, 
            AnalysisType(input_data.get("analysis_type", "creation"))
        )
        
        # Streaming generate
        async for chunk in client.generate_streaming(
            prompt=prompt,
            model=model_selection["model"],
            correlation_id=correlation_id
        ):
            yield chunk
    
    async def validate_ai_setup(self) -> Dict[str, Any]:
        """AI setup doğrulaması"""
        
        results = {
            "openai": {"available": False, "error": None},
            "vertex_ai": {"available": False, "error": None}
        }
        
        # OpenAI test
        try:
            openai_client = await self._get_openai_client()
            if openai_client:
                results["openai"]["available"] = await openai_client.validate_api_key()
        except Exception as e:
            results["openai"]["error"] = str(e)
        
        # Vertex AI test
        try:
            vertex_client = await self._get_vertex_client()
            if vertex_client:
                results["vertex_ai"]["available"] = await vertex_client.validate_credentials()
        except Exception as e:
            results["vertex_ai"]["error"] = str(e)
        
        return results


# Backward compatibility
class AIService(EnhancedAIService):
    """Legacy class alias"""
    pass
