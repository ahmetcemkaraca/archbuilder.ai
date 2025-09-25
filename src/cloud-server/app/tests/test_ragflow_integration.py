"""
RAGFlow Integration Tests

Bu modül RAGFlow entegrasyonu için kapsamlı testleri içerir.
respx/mock kullanarak RAGFlow API'sini mock'lar ve gerçek entegrasyon senaryolarını test eder.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx
from fastapi import FastAPI
from httpx import AsyncClient

from app.ai.ragflow.client import RAGFlowClient
from app.services.rag_service import RAGService


class TestRAGFlowClient:
    """RAGFlow client testleri - respx mock kullanarak"""

    @pytest.fixture
    def mock_ragflow_base_url(self):
        return "http://mock-ragflow:8000"

    @pytest.fixture
    def ragflow_client(self, mock_ragflow_base_url):
        return RAGFlowClient(
            base_url=mock_ragflow_base_url,
            api_key="test-api-key",
            timeout_seconds=30
        )

    @respx.mock
    async def test_create_dataset_success(self, ragflow_client):
        """Dataset oluşturma başarılı test"""
        # Mock response
        mock_response = {
            "success": True,
            "data": {
                "id": "dataset_123",
                "name": "test-dataset",
                "created_at": "2025-01-10T10:00:00Z"
            }
        }
        
        respx.post("http://mock-ragflow:8000/api/v1/datasets").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        async with ragflow_client as client:
            result = await client.create_dataset("test-dataset", correlation_id="test_corr_123")
            
            assert result["success"] is True
            assert result["data"]["id"] == "dataset_123"
            assert result["data"]["name"] == "test-dataset"

    @respx.mock
    async def test_create_dataset_failure(self, ragflow_client):
        """Dataset oluşturma hata testi"""
        respx.post("http://mock-ragflow:8000/api/v1/datasets").mock(
            return_value=httpx.Response(400, json={"error": "Invalid dataset name"})
        )
        
        async with ragflow_client as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.create_dataset("invalid-name", correlation_id="test_corr_123")

    @respx.mock
    async def test_upload_documents_success(self, ragflow_client):
        """Doküman yükleme başarılı test"""
        mock_response = {
            "success": True,
            "data": {
                "document_ids": ["doc_1", "doc_2"],
                "uploaded_count": 2
            }
        }
        
        respx.post("http://mock-ragflow:8000/api/v1/datasets/dataset_123/documents").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        # Test dosyaları
        files = [b"test content 1", b"test content 2"]
        filenames = ["test1.pdf", "test2.pdf"]
        
        async with ragflow_client as client:
            result = await client.upload_documents(
                dataset_id="dataset_123",
                files=files,
                filenames=filenames,
                correlation_id="test_corr_123"
            )
            
            assert result["success"] is True
            assert len(result["data"]["document_ids"]) == 2
            assert result["data"]["uploaded_count"] == 2

    @respx.mock
    async def test_parse_documents_success(self, ragflow_client):
        """Doküman parse etme başarılı test"""
        mock_response = {
            "success": True,
            "data": {
                "job_id": "parse_job_123",
                "status": "processing",
                "document_count": 2
            }
        }
        
        respx.post("http://mock-ragflow:8000/api/v1/datasets/dataset_123/chunks").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        async with ragflow_client as client:
            result = await client.parse_documents(
                dataset_id="dataset_123",
                document_ids=["doc_1", "doc_2"],
                options={"chunk_size": 1000, "overlap": 200},
                correlation_id="test_corr_123"
            )
            
            assert result["success"] is True
            assert result["data"]["job_id"] == "parse_job_123"
            assert result["data"]["status"] == "processing"

    @respx.mock
    async def test_retrieval_success(self, ragflow_client):
        """Retrieval başarılı test"""
        mock_response = {
            "success": True,
            "data": {
                "results": [
                    {
                        "content": "Test content 1",
                        "score": 0.95,
                        "document_id": "doc_1",
                        "chunk_id": "chunk_1"
                    },
                    {
                        "content": "Test content 2", 
                        "score": 0.87,
                        "document_id": "doc_2",
                        "chunk_id": "chunk_2"
                    }
                ],
                "total_results": 2
            }
        }
        
        respx.post("http://mock-ragflow:8000/api/v1/retrieval").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        async with ragflow_client as client:
            result = await client.retrieval(
                question="Test question",
                dataset_ids=["dataset_123"],
                top_k=5,
                vector_similarity_weight=0.7,
                correlation_id="test_corr_123"
            )
            
            assert result["success"] is True
            assert len(result["data"]["results"]) == 2
            assert result["data"]["total_results"] == 2
            assert result["data"]["results"][0]["score"] == 0.95

    @respx.mock
    async def test_retrieval_with_retry(self, ragflow_client):
        """Retrieval retry mekanizması testi"""
        # İlk iki çağrı 429 döner, üçüncü başarılı
        responses = [
            httpx.Response(429, json={"error": "Rate limited"}),
            httpx.Response(503, json={"error": "Service unavailable"}),
            httpx.Response(200, json={
                "success": True,
                "data": {"results": [], "total_results": 0}
            })
        ]
        
        respx.post("http://mock-ragflow:8000/api/v1/retrieval").mock(side_effect=responses)
        
        async with ragflow_client as client:
            result = await client.retrieval(
                question="Test question",
                dataset_ids=["dataset_123"],
                correlation_id="test_corr_123"
            )
            
            assert result["success"] is True

    @respx.mock
    async def test_ensure_dataset_creates_new(self, ragflow_client):
        """ensure_dataset yeni dataset oluşturma testi"""
        mock_response = {
            "success": True,
            "data": {
                "id": "new_dataset_123",
                "name": "preferred-name"
            }
        }
        
        respx.post("http://mock-ragflow:8000/api/v1/datasets").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        async with ragflow_client as client:
            dataset_id = await client.ensure_dataset("preferred-name", correlation_id="test_corr_123")
            
            assert dataset_id == "new_dataset_123"

    async def test_correlation_id_headers(self, ragflow_client):
        """Correlation ID header'larının doğru gönderilmesi testi"""
        correlation_id = "test_correlation_123"
        
        with respx.mock as mock:
            mock.post("http://mock-ragflow:8000/api/v1/datasets").mock(
                return_value=httpx.Response(200, json={"success": True, "data": {"id": "test"}})
            )
            
            async with ragflow_client as client:
                await client.create_dataset("test", correlation_id=correlation_id)
                
                # Request'in correlation ID header'ı içerdiğini kontrol et
                request = mock.calls[0].request
                assert request.headers["X-Correlation-ID"] == correlation_id

    async def test_client_context_manager(self, ragflow_client):
        """Client context manager testi"""
        with respx.mock as mock:
            mock.post("http://mock-ragflow:8000/api/v1/datasets").mock(
                return_value=httpx.Response(200, json={"success": True, "data": {"id": "test"}})
            )
            
            async with ragflow_client as client:
                assert client._client is not None
                await client.create_dataset("test")
            
            # Context manager'dan çıktıktan sonra client kapatılmalı
            assert ragflow_client._client is None


class TestRAGServiceIntegration:
    """RAGService entegrasyon testleri"""

    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAGService instance"""
        service = MagicMock(spec=RAGService)
        service.ensure_dataset = AsyncMock()
        service.upload_and_parse = AsyncMock()
        service.hybrid_search = AsyncMock()
        return service

    async def test_rag_service_ensure_dataset(self, mock_rag_service):
        """RAGService ensure_dataset testi"""
        mock_rag_service.ensure_dataset.return_value = {
            "success": True,
            "data": {"dataset_id": "test_dataset_123"}
        }
        
        result = await mock_rag_service.ensure_dataset(
            owner_id="user_123",
            project_id="project_123", 
            preferred_name="test-dataset"
        )
        
        assert result["success"] is True
        assert result["data"]["dataset_id"] == "test_dataset_123"
        mock_rag_service.ensure_dataset.assert_called_once()

    async def test_rag_service_hybrid_search(self, mock_rag_service):
        """RAGService hybrid_search testi"""
        mock_rag_service.hybrid_search.return_value = {
            "success": True,
            "data": {
                "results": [
                    {
                        "content": "Test architectural content",
                        "score": 0.92,
                        "source": "building_codes.pdf"
                    }
                ],
                "total_results": 1
            }
        }
        
        result = await mock_rag_service.hybrid_search(
            query="building codes requirements",
            dataset_ids=["dataset_123"],
            max_results=10
        )
        
        assert result["success"] is True
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["score"] == 0.92
        mock_rag_service.hybrid_search.assert_called_once()


class TestRAGEndpointsIntegration:
    """RAG endpoint'leri entegrasyon testleri"""

    async def test_rag_query_endpoint_success(self, app: FastAPI):
        """RAG query endpoint başarılı test"""
        with respx.mock as mock:
            # RAGFlow API mock
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {
                        "results": [
                            {
                                "content": "Test architectural content",
                                "score": 0.95,
                                "document_id": "doc_123"
                            }
                        ],
                        "total_results": 1
                    }
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "building codes",
                        "dataset_ids": ["dataset_123"],
                        "max_results": 5
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 1

    async def test_rag_query_endpoint_failure(self, app: FastAPI):
        """RAG query endpoint hata testi"""
        with respx.mock as mock:
            # RAGFlow API hata mock
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(500, json={"error": "Internal server error"})
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "building codes",
                        "dataset_ids": ["dataset_123"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                # Hata durumunda 502 Bad Gateway dönmeli
                assert response.status_code == 502

    async def test_hybrid_search_endpoint(self, app: FastAPI):
        """Hybrid search endpoint testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {
                        "results": [
                            {
                                "content": "Hybrid search result",
                                "score": 0.88,
                                "document_id": "doc_456"
                            }
                        ],
                        "total_results": 1
                    }
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/hybrid-search",
                    json={
                        "query": "architectural design",
                        "dataset_ids": ["dataset_123"],
                        "max_results": 10,
                        "keyword_boost": 0.4,
                        "dense_boost": 0.6
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 1

    async def test_ensure_dataset_endpoint(self, app: FastAPI):
        """Ensure dataset endpoint testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/datasets").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {
                        "id": "new_dataset_456",
                        "name": "project-dataset"
                    }
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/documents/rag/ensure-dataset",
                    json={
                        "owner_id": "user_123",
                        "project_id": "project_123",
                        "preferred_name": "project-dataset"
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["dataset_id"] == "new_dataset_456"

    async def test_upload_parse_async_endpoint(self, app: FastAPI):
        """Upload parse async endpoint testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/datasets/dataset_123/chunks").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {
                        "job_id": "parse_job_789",
                        "status": "processing"
                    }
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/documents/rag/dataset_123/upload-parse/async",
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "job_id" in data["data"]

    async def test_job_status_endpoint(self, app: FastAPI):
        """Job status endpoint testi"""
        with respx.mock as mock:
            mock.get("http://localhost:8000/api/v1/jobs/parse_job_789").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {
                        "job_id": "parse_job_789",
                        "status": "completed",
                        "progress": 100,
                        "result": {
                            "processed_documents": 5,
                            "created_chunks": 25
                        }
                    }
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/v1/documents/rag/jobs/parse_job_789",
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["status"] == "completed"
                assert data["data"]["progress"] == 100


class TestRAGErrorHandling:
    """RAG hata yönetimi testleri"""

    async def test_ragflow_connection_timeout(self, app: FastAPI):
        """RAGFlow bağlantı timeout testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={"query": "test query"},
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 502
                data = response.json()
                assert "timeout" in data["errors"][0]["message"].lower()

    async def test_ragflow_invalid_response_format(self, app: FastAPI):
        """RAGFlow geçersiz response format testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(200, json={"invalid": "format"})
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={"query": "test query"},
                    headers={"X-API-Key": "test-api-key"}
                )
                
                # Geçersiz format durumunda 502 dönmeli
                assert response.status_code == 502

    async def test_ragflow_rate_limiting(self, app: FastAPI):
        """RAGFlow rate limiting testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(429, json={"error": "Rate limit exceeded"})
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={"query": "test query"},
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 502
                data = response.json()
                assert "rate limit" in data["errors"][0]["message"].lower()


class TestRAGPerformance:
    """RAG performans testleri"""

    async def test_rag_query_performance(self, app: FastAPI):
        """RAG query performans testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {"results": [], "total_results": 0}
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                start_time = asyncio.get_event_loop().time()
                
                response = await ac.post(
                    "/v1/rag/query",
                    json={"query": "performance test"},
                    headers={"X-API-Key": "test-api-key"}
                )
                
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                assert response.status_code == 200
                # Response time 5 saniyeden az olmalı
                assert response_time < 5.0

    async def test_concurrent_rag_queries(self, app: FastAPI):
        """Eşzamanlı RAG query testi"""
        with respx.mock as mock:
            mock.post("http://localhost:8000/api/v1/retrieval").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "data": {"results": [], "total_results": 0}
                })
            )
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                # 5 eşzamanlı query gönder
                tasks = []
                for i in range(5):
                    task = ac.post(
                        "/v1/rag/query",
                        json={"query": f"concurrent test {i}"},
                        headers={"X-API-Key": "test-api-key"}
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                
                # Tüm response'lar başarılı olmalı
                for response in responses:
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
