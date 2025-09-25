"""
RAG Mock Response Tests

Bu modül RAG endpoint'leri için mock response testlerini içerir.
Gerçek RAGFlow bağlantısı olmadan endpoint'lerin doğru çalışmasını test eder.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.services.rag_service import RAGService
from app.ai.ragflow.client import RAGFlowClient


class TestRAGMockResponses:
    """RAG mock response testleri"""

    @pytest.fixture
    def mock_ragflow_responses(self):
        """RAGFlow mock response'ları"""
        return {
            "dataset_creation": {
                "success": True,
                "data": {
                    "id": "mock_dataset_123",
                    "name": "test-dataset",
                    "created_at": "2025-01-10T10:00:00Z"
                }
            },
            "document_upload": {
                "success": True,
                "data": {
                    "document_ids": ["doc_1", "doc_2"],
                    "uploaded_count": 2,
                    "status": "uploaded"
                }
            },
            "document_parse": {
                "success": True,
                "data": {
                    "job_id": "parse_job_123",
                    "status": "processing",
                    "document_count": 2,
                    "progress": 0
                }
            },
            "retrieval_success": {
                "success": True,
                "data": {
                    "results": [
                        {
                            "content": "Mock architectural content about building codes",
                            "score": 0.95,
                            "document_id": "doc_1",
                            "chunk_id": "chunk_1",
                            "source": "building_codes.pdf"
                        },
                        {
                            "content": "Mock content about structural requirements",
                            "score": 0.87,
                            "document_id": "doc_2", 
                            "chunk_id": "chunk_2",
                            "source": "structural_guide.pdf"
                        }
                    ],
                    "total_results": 2,
                    "query_time_ms": 150
                }
            },
            "hybrid_search": {
                "success": True,
                "data": {
                    "results": [
                        {
                            "content": "Hybrid search result combining keyword and vector search",
                            "score": 0.92,
                            "document_id": "doc_3",
                            "chunk_id": "chunk_3",
                            "source": "hybrid_doc.pdf",
                            "keyword_score": 0.8,
                            "vector_score": 0.95
                        }
                    ],
                    "total_results": 1,
                    "search_time_ms": 200
                }
            },
            "job_status_completed": {
                "success": True,
                "data": {
                    "job_id": "parse_job_123",
                    "status": "completed",
                    "progress": 100,
                    "result": {
                        "processed_documents": 2,
                        "created_chunks": 15,
                        "processing_time_ms": 5000
                    }
                }
            },
            "job_status_processing": {
                "success": True,
                "data": {
                    "job_id": "parse_job_123",
                    "status": "processing",
                    "progress": 65,
                    "current_document": "doc_2"
                }
            }
        }

    @pytest.fixture
    def mock_rag_service(self, mock_ragflow_responses):
        """Mock RAGService instance"""
        service = MagicMock(spec=RAGService)
        
        # Mock methods with realistic responses
        service.ensure_dataset = AsyncMock(return_value=mock_ragflow_responses["dataset_creation"])
        service.upload_and_parse = AsyncMock(return_value=mock_ragflow_responses["document_parse"])
        service.hybrid_search = AsyncMock(return_value=mock_ragflow_responses["hybrid_search"])
        service.get_job_status = AsyncMock(return_value=mock_ragflow_responses["job_status_completed"])
        
        return service

    async def test_rag_query_mock_success(self, app: FastAPI, mock_ragflow_responses):
        """RAG query mock başarılı test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=mock_ragflow_responses["retrieval_success"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "building codes requirements",
                        "dataset_ids": ["dataset_123"],
                        "max_results": 5
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 2
                assert data["data"]["results"][0]["score"] == 0.95

    async def test_rag_query_mock_empty_results(self, app: FastAPI):
        """RAG query mock boş sonuç testi"""
        empty_response = {
            "success": True,
            "data": {
                "results": [],
                "total_results": 0,
                "query_time_ms": 50
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=empty_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "nonexistent content",
                        "dataset_ids": ["dataset_123"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 0
                assert data["data"]["total_results"] == 0

    async def test_hybrid_search_mock_success(self, app: FastAPI, mock_ragflow_responses):
        """Hybrid search mock başarılı test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=mock_ragflow_responses["hybrid_search"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/hybrid-search",
                    json={
                        "query": "architectural design principles",
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
                assert data["data"]["results"][0]["score"] == 0.92

    async def test_ensure_dataset_mock_success(self, app: FastAPI, mock_ragflow_responses):
        """Ensure dataset mock başarılı test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.ensure_dataset = AsyncMock(return_value=mock_ragflow_responses["dataset_creation"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/documents/rag/ensure-dataset",
                    json={
                        "owner_id": "user_123",
                        "project_id": "project_123",
                        "preferred_name": "test-dataset"
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["dataset_id"] == "mock_dataset_123"

    async def test_upload_parse_async_mock_success(self, app: FastAPI, mock_ragflow_responses):
        """Upload parse async mock başarılı test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.upload_and_parse = AsyncMock(return_value=mock_ragflow_responses["document_parse"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/documents/rag/dataset_123/upload-parse/async",
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["job_id"] == "parse_job_123"
                assert data["data"]["status"] == "processing"

    async def test_job_status_mock_completed(self, app: FastAPI, mock_ragflow_responses):
        """Job status mock tamamlanmış test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_job_status = AsyncMock(return_value=mock_ragflow_responses["job_status_completed"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/v1/documents/rag/jobs/parse_job_123",
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["status"] == "completed"
                assert data["data"]["progress"] == 100

    async def test_job_status_mock_processing(self, app: FastAPI, mock_ragflow_responses):
        """Job status mock işleniyor test"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_job_status = AsyncMock(return_value=mock_ragflow_responses["job_status_processing"])
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/v1/documents/rag/jobs/parse_job_123",
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["status"] == "processing"
                assert data["data"]["progress"] == 65

    async def test_rag_query_mock_with_filters(self, app: FastAPI, mock_ragflow_responses):
        """RAG query mock filtrelerle test"""
        filtered_response = {
            "success": True,
            "data": {
                "results": [
                    {
                        "content": "Filtered architectural content",
                        "score": 0.90,
                        "document_id": "doc_filtered",
                        "chunk_id": "chunk_filtered",
                        "source": "filtered_doc.pdf"
                    }
                ],
                "total_results": 1,
                "filters_applied": {
                    "document_types": ["pdf"],
                    "languages": ["en"]
                }
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=filtered_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "filtered search",
                        "dataset_ids": ["dataset_123"],
                        "document_types": ["pdf"],
                        "languages": ["en"],
                        "filters": {
                            "date_range": "2024-01-01,2025-01-01"
                        }
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 1
                assert data["data"]["results"][0]["score"] == 0.90

    async def test_rag_query_mock_pagination(self, app: FastAPI):
        """RAG query mock sayfalama testi"""
        paginated_response = {
            "success": True,
            "data": {
                "results": [
                    {
                        "content": f"Paginated result {i}",
                        "score": 0.95 - (i * 0.05),
                        "document_id": f"doc_{i}",
                        "chunk_id": f"chunk_{i}"
                    }
                    for i in range(5)
                ],
                "total_results": 25,
                "page": 1,
                "per_page": 5,
                "total_pages": 5
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=paginated_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "paginated search",
                        "dataset_ids": ["dataset_123"],
                        "max_results": 5,
                        "page": 1
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["results"]) == 5
                assert data["data"]["total_results"] == 25

    async def test_rag_query_mock_error_handling(self, app: FastAPI):
        """RAG query mock hata yönetimi testi"""
        error_response = {
            "success": False,
            "error": {
                "code": "QUERY_ERROR",
                "message": "Invalid query parameters",
                "details": "Dataset ID not found"
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=error_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "error test",
                        "dataset_ids": ["nonexistent_dataset"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 400
                data = response.json()
                assert data["success"] is False
                assert "error" in data

    async def test_rag_query_mock_timeout(self, app: FastAPI):
        """RAG query mock timeout testi"""
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(side_effect=TimeoutError("Request timeout"))
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "timeout test",
                        "dataset_ids": ["dataset_123"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 502
                data = response.json()
                assert data["success"] is False
                assert "timeout" in data["errors"][0]["message"].lower()

    async def test_rag_query_mock_validation_error(self, app: FastAPI):
        """RAG query mock validation hatası testi"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Geçersiz request body
            response = await ac.post(
                "/v1/rag/query",
                json={
                    "query": "",  # Boş query
                    "dataset_ids": []  # Boş dataset listesi
                },
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "detail" in data

    async def test_rag_query_mock_unauthorized(self, app: FastAPI):
        """RAG query mock yetkisiz erişim testi"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # API key olmadan request
            response = await ac.post(
                "/v1/rag/query",
                json={
                    "query": "unauthorized test",
                    "dataset_ids": ["dataset_123"]
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "unauthorized" in data["detail"].lower()

    async def test_rag_query_mock_rate_limit(self, app: FastAPI):
        """RAG query mock rate limit testi"""
        rate_limit_response = {
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "retry_after": 60
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=rate_limit_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "rate limit test",
                        "dataset_ids": ["dataset_123"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                assert response.status_code == 429
                data = response.json()
                assert data["success"] is False
                assert "rate limit" in data["error"]["message"].lower()


class TestRAGMockPerformance:
    """RAG mock performans testleri"""

    async def test_rag_query_mock_performance(self, app: FastAPI):
        """RAG query mock performans testi"""
        import time
        
        performance_response = {
            "success": True,
            "data": {
                "results": [
                    {
                        "content": "Performance test result",
                        "score": 0.95,
                        "document_id": "perf_doc",
                        "chunk_id": "perf_chunk"
                    }
                ],
                "total_results": 1,
                "query_time_ms": 50,
                "cache_hit": True
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=performance_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                start_time = time.time()
                
                response = await ac.post(
                    "/v1/rag/query",
                    json={
                        "query": "performance test",
                        "dataset_ids": ["dataset_123"]
                    },
                    headers={"X-API-Key": "test-api-key"}
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                assert response.status_code == 200
                assert response_time < 1.0  # 1 saniyeden az olmalı
                
                data = response.json()
                assert data["success"] is True
                assert data["data"]["query_time_ms"] == 50

    async def test_rag_query_mock_concurrent_requests(self, app: FastAPI):
        """RAG query mock eşzamanlı istekler testi"""
        import asyncio
        
        concurrent_response = {
            "success": True,
            "data": {
                "results": [],
                "total_results": 0,
                "query_time_ms": 100
            }
        }
        
        with patch('app.services.rag_service.RAGService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.hybrid_search = AsyncMock(return_value=concurrent_response)
            mock_service_class.return_value = mock_service
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                # 10 eşzamanlı request
                tasks = []
                for i in range(10):
                    task = ac.post(
                        "/v1/rag/query",
                        json={
                            "query": f"concurrent test {i}",
                            "dataset_ids": ["dataset_123"]
                        },
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
