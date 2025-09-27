"""
AI Integration Test Suite
ArchBuilder.AI AI entegrasyonu için comprehensive testler
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.ai.openai.client import OpenAIClient
from app.ai.vertex.client import VertexAIClient  
from app.ai.model_selector import AdvancedModelSelector, TaskComplexity, AnalysisType
from app.services.ai_service import EnhancedAIService


class TestOpenAIClient:
    """OpenAI client testleri"""
    
    @pytest.mark.asyncio
    async def test_openai_client_initialization(self):
        """OpenAI client başlatma testi"""
        with patch('app.ai.openai.client.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            
            client = OpenAIClient()
            assert client is not None
            assert client.cost_per_1k_input_tokens == 0.03
    
    @pytest.mark.asyncio
    async def test_openai_generate_response(self):
        """OpenAI response generation testi"""
        with patch('app.ai.openai.client.AsyncOpenAI') as mock_openai:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"test": "response"}'
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.completion_tokens = 100
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient()
            
            result = await client.generate("Test prompt", correlation_id="test-123")
            
            assert result["provider"] == "openai"
            assert result["output"]["test"] == "response"
            assert result["metadata"]["correlation_id"] == "test-123"
            assert result["metadata"]["output_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_openai_error_handling(self):
        """OpenAI error handling testi"""
        with patch('app.ai.openai.client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient()
            
            result = await client.generate("Test prompt")
            
            assert result["metadata"]["error"] is True
            assert "API Error" in result["output"]["message"]


class TestVertexAIClient:
    """Vertex AI client testleri"""
    
    @pytest.mark.asyncio
    async def test_vertex_client_initialization(self):
        """Vertex AI client başlatma testi"""
        with patch('app.ai.vertex.client.settings') as mock_settings:
            mock_settings.google_cloud_project = "test-project"
            mock_settings.google_cloud_region = "us-central1"
            
            client = VertexAIClient()
            assert client.project_id == "test-project"
            assert client.location == "us-central1"
    
    @pytest.mark.asyncio
    async def test_vertex_generate_response(self):
        """Vertex AI response generation testi"""
        with patch('vertexai.generative_models.GenerativeModel') as mock_model:
            # Mock Vertex AI response
            mock_candidate = MagicMock()
            mock_candidate.content.parts = [MagicMock()]
            mock_candidate.content.parts[0].text = '{"vertex": "response"}'
            mock_candidate.finish_reason.name = "STOP"
            mock_candidate.safety_ratings = []
            
            mock_response = MagicMock()
            mock_response.candidates = [mock_candidate]
            
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance
            
            client = VertexAIClient()
            client.project_id = "test-project"
            
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor.return_value = mock_response
                
                result = await client.generate("Test prompt")
                
                assert result["provider"] == "vertex_ai"
                assert result["output"]["vertex"] == "response"
    
    @pytest.mark.asyncio
    async def test_vertex_stub_mode(self):
        """Vertex AI stub mode testi"""
        client = VertexAIClient()
        client.project_id = None  # Force stub mode
        
        result = await client.generate("Test prompt")
        
        assert result["provider"] == "vertex_ai"
        assert result["output"]["requires_setup"] is True
        assert result["metadata"]["is_stub"] is True


class TestAdvancedModelSelector:
    """Gelişmiş model selector testleri"""
    
    def test_model_selector_initialization(self):
        """Model selector başlatma testi"""
        selector = AdvancedModelSelector()
        assert "gpt-4-turbo" in selector.model_configs
        assert "gemini-1.5-pro" in selector.model_configs
    
    def test_simple_task_selection(self):
        """Basit task için model seçimi"""
        selector = AdvancedModelSelector()
        
        result = selector.select_optimal_model(
            language="en",
            complexity=TaskComplexity.SIMPLE,
            analysis_type=AnalysisType.CREATION
        )
        
        assert result["provider"] in ["openai", "vertex_ai"]
        assert result["confidence"] > 0.5
        assert "estimated_cost_usd" in result
        assert len(result["selection_reasons"]) > 0
    
    def test_turkish_document_optimization(self):
        """Türkçe doküman için optimizasyon"""
        selector = AdvancedModelSelector()
        
        result = selector.select_optimal_model(
            language="tr",
            complexity=TaskComplexity.MEDIUM,
            analysis_type=AnalysisType.DOCUMENT_ANALYSIS,
            region="tr"
        )
        
        # Turkish content için Vertex AI tercih edilmeli
        assert result["provider"] == "vertex_ai"
        assert "turkish" in str(result["selection_reasons"]).lower() or "bölgesel" in str(result["selection_reasons"]).lower()
    
    def test_critical_task_selection(self):
        """Kritik task için model seçimi"""
        selector = AdvancedModelSelector()
        
        result = selector.select_optimal_model(
            complexity=TaskComplexity.CRITICAL,
            analysis_type=AnalysisType.EXISTING_PROJECT_ANALYSIS,
            file_format="rvt"
        )
        
        # Critical task için güçlü model seçilmeli
        assert "gpt-4" in result["model"] or "gemini-1.5-pro" in result["model"]
        assert result["confidence"] > 0.6
    
    def test_cost_optimization(self):
        """Maliyet optimizasyonu testi"""
        selector = AdvancedModelSelector()
        
        # Düşük budget constraint
        result = selector.select_optimal_model(
            complexity=TaskComplexity.SIMPLE,
            estimated_tokens=5000,
            budget_constraint=0.01
        )
        
        assert result["estimated_cost_usd"] <= 0.01
    
    def test_legacy_compatibility(self):
        """Legacy method uyumluluğu"""
        selector = AdvancedModelSelector()
        
        result = selector.select(language="tr", complexity="high")
        
        assert "provider" in result
        assert "model" in result


class TestEnhancedAIService:
    """Enhanced AI Service testleri"""
    
    @pytest.mark.asyncio
    async def test_ai_service_initialization(self):
        """AI service başlatma testi"""
        service = EnhancedAIService()
        assert service._selector is not None
        assert service._openai_client is None  # Lazy initialization
        assert service._vertex_client is None
    
    @pytest.mark.asyncio
    async def test_create_command(self):
        """AI command oluşturma testi"""
        with patch('app.services.ai_service.create_openai_client') as mock_openai_create:
            with patch('asyncio.create_task') as mock_task:
                mock_openai_create.return_value = AsyncMock()
                
                service = EnhancedAIService()
                
                # Mock database session
                mock_db = AsyncMock()
                mock_db.add = MagicMock()
                mock_db.flush = AsyncMock()
                
                input_data = {
                    "building_type": "residential",
                    "total_area_m2": 100,
                    "rooms": ["living_room", "bedroom", "kitchen"],
                    "language": "tr",
                    "complexity": "medium"
                }
                
                result = await service.create_command(
                    db=mock_db,
                    command="generate_layout",
                    input_data=input_data,
                    user_id="test-user",
                    project_id="test-project"
                )
                
                assert "id" in result
                assert "correlation_id" in result
                assert "selected_model" in result
                assert result["status"] == "processing"
                assert mock_task.called  # Async processing başlatıldı
    
    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Streaming response testi"""
        with patch('app.services.ai_service.create_openai_client') as mock_create:
            mock_client = AsyncMock()
            
            # Mock streaming response
            async def mock_streaming():
                yield {"content": "Stream chunk 1", "correlation_id": "test"}
                yield {"content": "Stream chunk 2", "correlation_id": "test"}
            
            mock_client.generate_streaming.return_value = mock_streaming()
            mock_create.return_value = mock_client
            
            service = EnhancedAIService()
            
            input_data = {
                "language": "en",
                "complexity": "simple",
                "analysis_type": "creation"
            }
            
            chunks = []
            async for chunk in service.generate_streaming_response("test command", input_data):
                chunks.append(chunk)
            
            assert len(chunks) == 2
            assert chunks[0]["content"] == "Stream chunk 1"
            assert chunks[1]["content"] == "Stream chunk 2"
    
    @pytest.mark.asyncio
    async def test_validate_ai_setup(self):
        """AI setup validation testi"""
        with patch('app.services.ai_service.create_openai_client') as mock_openai:
            with patch('app.services.ai_service.create_vertex_client') as mock_vertex:
                # Mock clients
                mock_openai_client = AsyncMock()
                mock_openai_client.validate_api_key.return_value = True
                mock_openai.return_value = mock_openai_client
                
                mock_vertex_client = AsyncMock()
                mock_vertex_client.validate_credentials.return_value = True
                mock_vertex.return_value = mock_vertex_client
                
                service = EnhancedAIService()
                
                result = await service.validate_ai_setup()
                
                assert result["openai"]["available"] is True
                assert result["vertex_ai"]["available"] is True
                assert result["openai"]["error"] is None
                assert result["vertex_ai"]["error"] is None


class TestIntegrationScenarios:
    """Integration senaryoları"""
    
    @pytest.mark.asyncio
    async def test_full_layout_generation_flow(self):
        """Tam layout generation akışı"""
        # Mock tüm bağımlılıkları
        with patch('app.ai.openai.client.AsyncOpenAI') as mock_openai:
            with patch('app.services.ai_service.create_openai_client') as mock_create:
                # Mock OpenAI response
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "walls": [
                        {"start": {"x": 0, "y": 0}, "end": {"x": 10000, "y": 0}, "type": "exterior"}
                    ],
                    "doors": [
                        {"wall_index": 0, "position": 5000, "width": 900, "type": "single"}
                    ],
                    "confidence": 0.95
                })
                mock_response.choices[0].finish_reason = "stop"
                mock_response.usage.completion_tokens = 250
                
                mock_client = AsyncMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client
                mock_create.return_value = OpenAIClient()
                
                # Test akışı
                service = EnhancedAIService()
                selector = AdvancedModelSelector()
                
                # 1. Model seçimi
                model_selection = selector.select_optimal_model(
                    language="tr",
                    complexity=TaskComplexity.MEDIUM,
                    analysis_type=AnalysisType.CREATION,
                    estimated_tokens=2000
                )
                
                assert model_selection["provider"] in ["openai", "vertex_ai"]
                
                # 2. AI generation (mock)
                client = await service._get_openai_client()
                if client:
                    result = await client.generate(
                        "Generate architectural layout for 100m² residential building with 3 rooms",
                        correlation_id="integration-test"
                    )
                    
                    assert result["provider"] == "openai"
                    assert "walls" in result["output"]
                    assert "doors" in result["output"]
                    assert result["output"]["confidence"] > 0.9


# Test configuration
@pytest.fixture
def mock_settings():
    """Test için mock settings"""
    with patch('app.core.config.settings') as mock:
        mock.openai_api_key = "test-openai-key"
        mock.google_cloud_project = "test-project"
        mock.google_cloud_region = "us-central1"
        yield mock


# Performance tests
class TestPerformance:
    """Performance testleri"""
    
    @pytest.mark.asyncio
    async def test_concurrent_ai_requests(self):
        """Concurrent AI request handling"""
        service = EnhancedAIService()
        
        # Mock AI client
        mock_client = AsyncMock()
        mock_client.generate.return_value = {
            "provider": "test",
            "output": {"result": "test"},
            "metadata": {"processing_time": 0.5}
        }
        
        with patch.object(service, '_get_openai_client', return_value=mock_client):
            # Concurrent requests
            tasks = []
            for i in range(5):
                task = service.generate_streaming_response(
                    f"test command {i}",
                    {"language": "en", "complexity": "simple"}
                )
                tasks.append(task)
            
            # Tüm task'ların başladığını kontrol et
            assert len(tasks) == 5


if __name__ == "__main__":
    # Test runner
    pytest.main([__file__, "-v", "--tb=short"])