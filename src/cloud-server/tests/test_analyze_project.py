import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.validation_service import ValidationService
from app.services.geometric_validator import GeometricValidator
from app.services.code_validator import CodeValidator


class TestAnalyzeProject:
    """TR: analyze_project fonksiyonu testleri - P18-T3"""
    
    @pytest.fixture
    async def validation_service(self):
        """TR: ValidationService fixture"""
        service = ValidationService()
        return service
    
    @pytest.fixture
    async def mock_db(self):
        """TR: Mock database session"""
        db = AsyncMock()
        db.flush = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_analyze_project_geometry_only(self, validation_service, mock_db):
        """TR: Sadece geometri analizi testi"""
        # TR: Test verileri
        project_id = "test-project-123"
        analysis_type = "geometry"
        options = {"region": "TR"}
        
        # TR: Mock geometric validator
        mock_geometric_result = {
            "project_id": project_id,
            "valid": True,
            "geometry_summary": {
                "total_rooms": 5,
                "total_area": 120.0,
                "floor_count": 2,
                "structure_type": "concrete"
            },
            "issues": [],
            "recommendations": ["TR: Tasarım optimize edilebilir"],
            "confidence_score": 0.85
        }
        
        validation_service._geometric_validator.analyze_project = AsyncMock(
            return_value=mock_geometric_result
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True
        assert "geometry_analysis" in result["data"]
        assert "code_analysis" not in result["data"]
        assert result["data"]["geometry_analysis"]["valid"] is True
        assert result["data"]["geometry_analysis"]["total_rooms"] == 5
        assert result["data"]["confidence_score"] == 0.5  # TR: Sadece geometri analizi
        assert len(result["data"]["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_project_code_only(self, validation_service, mock_db):
        """TR: Sadece kod analizi testi"""
        # TR: Test verileri
        project_id = "test-project-456"
        analysis_type = "code"
        options = {"region": "US"}
        
        # TR: Mock code validator
        mock_code_result = {
            "project_id": project_id,
            "valid": True,
            "code_compliance": {
                "region": "US",
                "compliance_score": 0.9,
                "requirements_met": 8,
                "total_requirements": 9,
                "critical_violations": 0,
                "warnings": 1
            },
            "issues": [],
            "recommendations": ["TR: Yangın güvenliği sistemi eklenmeli"],
            "confidence_score": 0.9
        }
        
        validation_service._code_validator.analyze_project = AsyncMock(
            return_value=mock_code_result
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True
        assert "code_analysis" in result["data"]
        assert "geometry_analysis" not in result["data"]
        assert result["data"]["code_analysis"]["valid"] is True
        assert result["data"]["code_analysis"]["compliance_score"] == 0.9
        assert result["data"]["confidence_score"] == 0.5  # TR: Sadece kod analizi
        assert len(result["data"]["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_project_both_types(self, validation_service, mock_db):
        """TR: Hem geometri hem kod analizi testi"""
        # TR: Test verileri
        project_id = "test-project-789"
        analysis_type = "both"
        options = {"region": "TR", "building_type": "residential"}
        
        # TR: Mock geometric validator
        mock_geometric_result = {
            "project_id": project_id,
            "valid": True,
            "geometry_summary": {
                "total_rooms": 4,
                "total_area": 95.0,
                "floor_count": 1,
                "structure_type": "concrete"
            },
            "issues": [],
            "recommendations": [],
            "confidence_score": 0.8
        }
        
        # TR: Mock code validator
        mock_code_result = {
            "project_id": project_id,
            "valid": True,
            "code_compliance": {
                "region": "TR",
                "compliance_score": 0.85,
                "requirements_met": 7,
                "total_requirements": 8,
                "critical_violations": 0,
                "warnings": 1
            },
            "issues": [],
            "recommendations": ["TR: Erişilebilirlik önlemleri gözden geçirilmeli"],
            "confidence_score": 0.85
        }
        
        validation_service._geometric_validator.analyze_project = AsyncMock(
            return_value=mock_geometric_result
        )
        validation_service._code_validator.analyze_project = AsyncMock(
            return_value=mock_code_result
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True
        assert "geometry_analysis" in result["data"]
        assert "code_analysis" in result["data"]
        assert result["data"]["geometry_analysis"]["valid"] is True
        assert result["data"]["code_analysis"]["valid"] is True
        assert result["data"]["confidence_score"] == 1.0  # TR: Her iki analiz de başarılı
        assert len(result["data"]["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_project_geometric_failure(self, validation_service, mock_db):
        """TR: Geometri analizi başarısızlık testi"""
        # TR: Test verileri
        project_id = "test-project-fail"
        analysis_type = "both"
        options = {"region": "TR"}
        
        # TR: Mock geometric validator - başarısız
        mock_geometric_result = {
            "project_id": project_id,
            "valid": False,
            "geometry_summary": {},
            "issues": ["TR: Geometrik validasyon başarısız"],
            "recommendations": [],
            "confidence_score": 0.0
        }
        
        # TR: Mock code validator - başarılı
        mock_code_result = {
            "project_id": project_id,
            "valid": True,
            "code_compliance": {
                "region": "TR",
                "compliance_score": 0.8,
                "requirements_met": 6,
                "total_requirements": 8,
                "critical_violations": 0,
                "warnings": 2
            },
            "issues": [],
            "recommendations": [],
            "confidence_score": 0.8
        }
        
        validation_service._geometric_validator.analyze_project = AsyncMock(
            return_value=mock_geometric_result
        )
        validation_service._code_validator.analyze_project = AsyncMock(
            return_value=mock_code_result
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True
        assert result["data"]["geometry_analysis"]["valid"] is False
        assert result["data"]["code_analysis"]["valid"] is True
        assert result["data"]["confidence_score"] == 0.5  # TR: Sadece kod analizi başarılı
        assert "TR: Geometrik validasyon başarısız" in result["data"]["recommendations"]
    
    @pytest.mark.asyncio
    async def test_analyze_project_invalid_request_schema(self, validation_service, mock_db):
        """TR: Geçersiz istek schema testi"""
        # TR: Test verileri - geçersiz analysis_type
        project_id = "test-project-invalid"
        analysis_type = "invalid_type"  # TR: Geçersiz tip
        options = {"region": "TR"}
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is False
        assert "error" in result["data"]
        assert "Geçersiz istek formatı" in result["data"]["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_project_geometric_exception(self, validation_service, mock_db):
        """TR: Geometri analizi exception testi"""
        # TR: Test verileri
        project_id = "test-project-exception"
        analysis_type = "geometry"
        options = {"region": "TR"}
        
        # TR: Mock geometric validator - exception fırlat
        validation_service._geometric_validator.analyze_project = AsyncMock(
            side_effect=Exception("TR: Geometri analizi hatası")
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True  # TR: Exception handle edildi
        assert "geometry_analysis" in result["data"]
        assert "error" in result["data"]["geometry_analysis"]
        assert "Geometri analizi hatası" in result["data"]["geometry_analysis"]["error"]
        assert result["data"]["confidence_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_project_code_exception(self, validation_service, mock_db):
        """TR: Kod analizi exception testi"""
        # TR: Test verileri
        project_id = "test-project-code-exception"
        analysis_type = "code"
        options = {"region": "TR"}
        
        # TR: Mock code validator - exception fırlat
        validation_service._code_validator.analyze_project = AsyncMock(
            side_effect=Exception("TR: Kod analizi hatası")
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True  # TR: Exception handle edildi
        assert "code_analysis" in result["data"]
        assert "error" in result["data"]["code_analysis"]
        assert "Kod analizi hatası" in result["data"]["code_analysis"]["error"]
        assert result["data"]["confidence_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_project_low_confidence_recommendations(self, validation_service, mock_db):
        """TR: Düşük güven skoru önerileri testi"""
        # TR: Test verileri
        project_id = "test-project-low-confidence"
        analysis_type = "both"
        options = {"region": "TR"}
        
        # TR: Mock geometric validator - düşük confidence
        mock_geometric_result = {
            "project_id": project_id,
            "valid": False,
            "geometry_summary": {},
            "issues": ["TR: Geometrik problem"],
            "recommendations": [],
            "confidence_score": 0.3
        }
        
        # TR: Mock code validator - düşük confidence
        mock_code_result = {
            "project_id": project_id,
            "valid": False,
            "code_compliance": {
                "region": "TR",
                "compliance_score": 0.4,
                "requirements_met": 2,
                "total_requirements": 8,
                "critical_violations": 2,
                "warnings": 4
            },
            "issues": ["TR: Kod ihlalleri"],
            "recommendations": [],
            "confidence_score": 0.4
        }
        
        validation_service._geometric_validator.analyze_project = AsyncMock(
            return_value=mock_geometric_result
        )
        validation_service._code_validator.analyze_project = AsyncMock(
            return_value=mock_code_result
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is True
        assert result["data"]["confidence_score"] == 0.0  # TR: Her iki analiz de başarısız
        assert len(result["data"]["recommendations"]) >= 3  # TR: En az 3 öneri
        assert "TR: Proje analizi eksik, daha detaylı inceleme önerilir" in result["data"]["recommendations"]
        assert "TR: Geometrik validasyon başarısız" in result["data"]["recommendations"]
        assert "TR: Kod validasyonu başarısız" in result["data"]["recommendations"]
    
    @pytest.mark.asyncio
    async def test_analyze_project_service_exception(self, validation_service, mock_db):
        """TR: Service level exception testi"""
        # TR: Test verileri
        project_id = "test-project-service-exception"
        analysis_type = "both"
        options = {"region": "TR"}
        
        # TR: Mock db.flush exception fırlat
        mock_db.flush.side_effect = Exception("TR: Database hatası")
        
        # TR: Mock validators
        validation_service._geometric_validator.analyze_project = AsyncMock(
            return_value={"valid": True, "confidence_score": 0.8}
        )
        validation_service._code_validator.analyze_project = AsyncMock(
            return_value={"valid": True, "confidence_score": 0.8}
        )
        
        # TR: Test çalıştır
        result = await validation_service.analyze_project(
            db=mock_db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options
        )
        
        # TR: Assertions
        assert result["success"] is False
        assert "error" in result["data"]
        assert "Database hatası" in result["data"]["error"]
