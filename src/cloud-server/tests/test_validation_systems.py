import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.validation_service import ValidationService
from app.services.geometric_validator import GeometricValidator
from app.services.code_validator import CodeValidator


class TestValidationSystems:
    """TR: Validation sistemleri testleri"""
    
    @pytest.fixture
    async def validation_service(self):
        """TR: ValidationService fixture"""
        service = ValidationService()
        return service
    
    @pytest.fixture
    async def geometric_validator(self):
        """TR: GeometricValidator fixture"""
        validator = GeometricValidator()
        return validator
    
    @pytest.fixture
    async def code_validator(self):
        """TR: CodeValidator fixture"""
        validator = CodeValidator()
        return validator
    
    @pytest.fixture
    async def mock_db(self):
        """TR: Mock database session"""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db
    
    # TR: JSON Schema Validation Tests
    @pytest.mark.asyncio
    async def test_validate_json_schema_valid(self, validation_service):
        """TR: Geçerli JSON schema validation testi"""
        data = {
            "payload": {"rooms": [{"type": "bedroom", "area": 15}]},
            "building_type": "residential"
        }
        schema_name = "ValidationRequest"
        
        result = await validation_service.validate_json_schema(data, schema_name)
        
        assert result["success"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_json_schema_invalid(self, validation_service):
        """TR: Geçersiz JSON schema validation testi"""
        data = {
            "invalid_field": "test"
            # TR: payload eksik
        }
        schema_name = "ValidationRequest"
        
        result = await validation_service.validate_json_schema(data, schema_name)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert any("payload" in error["message"] for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_validate_json_schema_unknown_schema(self, validation_service):
        """TR: Bilinmeyen schema testi"""
        data = {"test": "data"}
        schema_name = "UnknownSchema"
        
        result = await validation_service.validate_json_schema(data, schema_name)
        
        assert result["success"] is False
        assert "Bilinmeyen schema" in result["errors"][0]
    
    # TR: Geometric Validation Tests
    @pytest.mark.asyncio
    async def test_geometric_validation_valid_rooms(self, geometric_validator):
        """TR: Geçerli oda geometrisi testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15, "length": 5, "width": 3, "height": 2.5},
                {"type": "bathroom", "area": 8, "length": 4, "width": 2, "height": 2.4}
            ]
        }
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "rooms" in result["validations"]
        assert result["validations"]["rooms"]["room_count"] == 2
    
    @pytest.mark.asyncio
    async def test_geometric_validation_invalid_room_area(self, geometric_validator):
        """TR: Geçersiz oda alanı testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 3},  # TR: Çok küçük alan
                {"type": "bathroom", "area": 150}  # TR: Çok büyük alan
            ]
        }
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("çok küçük" in error.lower() for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_geometric_validation_no_rooms(self, geometric_validator):
        """TR: Oda olmayan testi"""
        payload = {"dimensions": {"total_area": 100}}
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is False
        assert any("En az bir oda tanımlanmalı" in error for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_geometric_validation_height_issues(self, geometric_validator):
        """TR: Yükseklik problemleri testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15, "height": 2.0},  # TR: Çok düşük
                {"type": "bathroom", "area": 8, "height": 4.5}   # TR: Çok yüksek
            ]
        }
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("çok düşük" in error.lower() for error in result["errors"])
        assert len(result["warnings"]) > 0
        assert any("çok yüksek" in warning.lower() for warning in result["warnings"])
    
    @pytest.mark.asyncio
    async def test_geometric_validation_residential_requirements(self, geometric_validator):
        """TR: Konut gereksinimleri testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15},
                {"type": "kitchen", "area": 12}
                # TR: Banyo eksik
            ]
        }
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is False
        assert any("banyo bulunamadı" in error.lower() for error in result["errors"])
    
    # TR: Code Validation Tests
    @pytest.mark.asyncio
    async def test_code_validation_tr_residential(self, code_validator):
        """TR: Türkiye konut kodu validation testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15, "window_area": 2},
                {"type": "bathroom", "area": 8, "window_area": 1},
                {"type": "kitchen", "area": 12, "window_area": 1.5}
            ],
            "dimensions": {"height": 2.5}
        }
        building_type = "residential"
        region = "TR"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is True
        assert result["region"] == region
        assert result["building_type"] == building_type
        assert "code_compliance" in result
        assert result["code_compliance"]["region"] == region
    
    @pytest.mark.asyncio
    async def test_code_validation_us_commercial(self, code_validator):
        """TR: ABD ticari kodu validation testi"""
        payload = {
            "rooms": [
                {"type": "office", "area": 200, "window_area": 30},
                {"type": "restroom", "area": 150, "window_area": 25}
            ],
            "dimensions": {"height": 10}  # TR: feet
        }
        building_type = "commercial"
        region = "US"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is True
        assert result["region"] == region
        assert result["building_type"] == building_type
    
    @pytest.mark.asyncio
    async def test_code_validation_insufficient_window_area(self, code_validator):
        """TR: Yetersiz pencere alanı testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15, "window_area": 0.5}  # TR: Yetersiz pencere
            ]
        }
        building_type = "residential"
        region = "TR"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is False
        assert any("pencere alanı yetersiz" in error.lower() for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_code_validation_missing_required_rooms(self, code_validator):
        """TR: Eksik gerekli odalar testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15}
                # TR: Banyo ve mutfak eksik
            ]
        }
        building_type = "residential"
        region = "TR"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is False
        assert any("banyo bulunamadı" in error.lower() for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_code_validation_unknown_region(self, code_validator):
        """TR: Bilinmeyen bölge testi"""
        payload = {"rooms": []}
        building_type = "residential"
        region = "UNKNOWN"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is False
        assert any("Desteklenmeyen bölge" in error for error in result["errors"])
    
    # TR: Comprehensive Validation Tests
    @pytest.mark.asyncio
    async def test_comprehensive_validation_success(self, validation_service, mock_db):
        """TR: Kapsamlı validation başarı testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 15, "length": 5, "width": 3, "height": 2.5, "window_area": 2},
                {"type": "bathroom", "area": 8, "length": 4, "width": 2, "height": 2.4, "window_area": 1},
                {"type": "kitchen", "area": 12, "length": 4, "width": 3, "height": 2.5, "window_area": 1.5}
            ],
            "dimensions": {"total_area": 35, "height": 2.5}
        }
        building_type = "residential"
        validation_types = ["schema", "geometric", "code"]
        
        result = await validation_service.validate_comprehensive(
            db=mock_db,
            payload=payload,
            building_type=building_type,
            validation_types=validation_types
        )
        
        assert result["success"] is True
        assert "validation_id" in result["data"]
        assert "results" in result["data"]
        assert len(result["data"]["results"]) == 3  # TR: 3 validation tipi
        assert result["data"]["overall_success"] is True
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_failure(self, validation_service, mock_db):
        """TR: Kapsamlı validation başarısızlık testi"""
        payload = {
            "rooms": [
                {"type": "bedroom", "area": 3},  # TR: Çok küçük
                {"type": "kitchen", "area": 5}   # TR: Banyo eksik
            ]
        }
        building_type = "residential"
        validation_types = ["schema", "geometric", "code"]
        
        result = await validation_service.validate_comprehensive(
            db=mock_db,
            payload=payload,
            building_type=building_type,
            validation_types=validation_types
        )
        
        assert result["success"] is False
        assert "validation_id" in result["data"]
        assert "results" in result["data"]
        assert result["data"]["overall_success"] is False
    
    # TR: Edge Cases and Error Handling
    @pytest.mark.asyncio
    async def test_validation_service_exception_handling(self, validation_service):
        """TR: Validation service exception handling testi"""
        # TR: Geçersiz schema ile test
        data = {"invalid": "data"}
        schema_name = "ValidationRequest"
        
        # TR: Exception fırlatacak şekilde mock
        validation_service._validators = {}
        
        result = await validation_service.validate_json_schema(data, schema_name)
        
        assert result["success"] is False
        assert "Bilinmeyen schema" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_geometric_validator_exception_handling(self, geometric_validator):
        """TR: Geometric validator exception handling testi"""
        # TR: Geçersiz payload ile test
        payload = None
        building_type = "residential"
        
        result = await geometric_validator.validate(payload, building_type)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Validation hatası" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_code_validator_exception_handling(self, code_validator):
        """TR: Code validator exception handling testi"""
        # TR: Geçersiz payload ile test
        payload = None
        building_type = "residential"
        region = "TR"
        
        result = await code_validator.validate(payload, building_type, region)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Validation hatası" in result["errors"][0]
