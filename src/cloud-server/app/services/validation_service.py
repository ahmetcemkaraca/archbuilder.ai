from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union
from jsonschema import Draft7Validator, ValidationError, SchemaError
from jsonschema.validators import extend

from app.database.session import AsyncSession
from app.database.models.validation_result import ValidationResult
from app.services.geometric_validator import GeometricValidator
from app.services.code_validator import CodeValidator

logger = logging.getLogger(__name__)


class ValidationService:
    """TR: JSON schema validation ve geometric/code validation servisi"""
    
    def __init__(self):
        self._geometric_validator = GeometricValidator()
        self._code_validator = CodeValidator()
        self._validators: Dict[str, Draft7Validator] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """TR: Registry'den schema'ları yükle ve validator'ları oluştur"""
        try:
            # TR: Temel schema'ları yükle
            schemas = {
                "AICommandPreview": {
                    "type": "object",
                    "properties": {
                        "selectedModel": {"type": "object"},
                        "prompt": {"type": "string"},
                        "preview": {"type": "object"}
                    }
                },
                "ValidationRequest": {
                    "type": "object",
                    "properties": {
                        "payload": {"type": "object"},
                        "building_type": {"type": "string"}
                    },
                    "required": ["payload"]
                },
                "ValidationResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"}
                    },
                    "required": ["success", "data"]
                },
                "ProjectAnalysisRequest": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string"},
                        "analysis_type": {"type": "string", "enum": ["geometry", "code", "both"]},
                        "options": {"type": "object"}
                    },
                    "required": ["project_id", "analysis_type"]
                },
                "ProjectAnalysisResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "geometry_analysis": {"type": "object"},
                                "code_analysis": {"type": "object"},
                                "recommendations": {"type": "array", "items": {"type": "string"}},
                                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    },
                    "required": ["success", "data"]
                }
            }
            
            for schema_name, schema_def in schemas.items():
                try:
                    self._validators[schema_name] = Draft7Validator(schema_def)
                    logger.info(f"TR: Schema yüklendi: {schema_name}")
                except SchemaError as e:
                    logger.error(f"TR: Schema hatası {schema_name}: {e}")
                    
        except Exception as e:
            logger.error(f"TR: Schema yükleme hatası: {e}")
    
    async def validate_json_schema(
        self, 
        data: Any, 
        schema_name: str
    ) -> Dict[str, Any]:
        """TR: JSON schema validation"""
        try:
            if schema_name not in self._validators:
                return {
                    "success": False,
                    "errors": [f"TR: Bilinmeyen schema: {schema_name}"]
                }
            
            validator = self._validators[schema_name]
            errors = list(validator.iter_errors(data))
            
            if not errors:
                return {"success": True, "errors": []}
            
            error_details = []
            for error in errors:
                error_details.append({
                    "path": " -> ".join(str(p) for p in error.absolute_path),
                    "message": error.message,
                    "schema_path": " -> ".join(str(p) for p in error.schema_path)
                })
            
            return {
                "success": False,
                "errors": error_details
            }
            
        except Exception as e:
            logger.error(f"TR: JSON schema validation hatası: {e}")
            return {
                "success": False,
                "errors": [f"TR: Validation hatası: {str(e)}"]
            }
    
    async def validate_geometric(
        self, 
        payload: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Geometric validation"""
        try:
            result = await self._geometric_validator.validate(payload, building_type)
            return {
                "success": result.get("valid", False),
                "data": result
            }
        except Exception as e:
            logger.error(f"TR: Geometric validation hatası: {e}")
            return {
                "success": False,
                "data": {"error": str(e)}
            }
    
    async def validate_code(
        self, 
        payload: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Code validation"""
        try:
            result = await self._code_validator.validate(payload, building_type)
            return {
                "success": result.get("valid", False),
                "data": result
            }
        except Exception as e:
            logger.error(f"TR: Code validation hatası: {e}")
            return {
                "success": False,
                "data": {"error": str(e)}
            }
    
    async def validate_comprehensive(
        self,
        db: AsyncSession,
        payload: Dict[str, Any],
        building_type: str,
        validation_types: List[str] = ["schema", "geometric", "code"]
    ) -> Dict[str, Any]:
        """TR: Kapsamlı validation - schema, geometric ve code"""
        try:
            results = {}
            
            # TR: JSON schema validation
            if "schema" in validation_types:
                schema_result = await self.validate_json_schema(payload, "ValidationRequest")
                results["schema"] = schema_result
            
            # TR: Geometric validation
            if "geometric" in validation_types:
                geometric_result = await self.validate_geometric(payload, building_type)
                results["geometric"] = geometric_result
            
            # TR: Code validation
            if "code" in validation_types:
                code_result = await self.validate_code(payload, building_type)
                results["code"] = code_result
            
            # TR: Sonuçları veritabanına kaydet
            validation_record = ValidationResult(
                payload=payload,
                building_type=building_type,
                results=results,
                overall_success=all(
                    result.get("success", False) 
                    for result in results.values()
                )
            )
            db.add(validation_record)
            await db.flush()
            
            return {
                "success": validation_record.overall_success,
                "data": {
                    "validation_id": validation_record.id,
                    "results": results,
                    "overall_success": validation_record.overall_success
                }
            }
            
        except Exception as e:
            logger.error(f"TR: Kapsamlı validation hatası: {e}")
            return {
                "success": False,
                "data": {"error": str(e)}
            }
    
    async def analyze_project(
        self,
        db: AsyncSession,
        project_id: str,
        analysis_type: str = "both",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """TR: Proje analizi - P18-T1 implementasyonu"""
        try:
            if options is None:
                options = {}
            
            # TR: Schema validation
            request_data = {
                "project_id": project_id,
                "analysis_type": analysis_type,
                "options": options
            }
            
            schema_result = await self.validate_json_schema(request_data, "ProjectAnalysisRequest")
            if not schema_result["success"]:
                return {
                    "success": False,
                    "data": {"error": "TR: Geçersiz istek formatı", "details": schema_result["errors"]}
                }
            
            results = {
                "geometry_analysis": {},
                "code_analysis": {},
                "recommendations": [],
                "confidence_score": 0.0
            }
            
            # TR: Geometric analysis
            if analysis_type in ["geometry", "both"]:
                try:
                    geometry_result = await self._geometric_validator.analyze_project(project_id, options)
                    results["geometry_analysis"] = geometry_result
                except Exception as e:
                    logger.error(f"TR: Geometric analysis hatası: {e}")
                    results["geometry_analysis"] = {"error": str(e)}
            
            # TR: Code analysis
            if analysis_type in ["code", "both"]:
                try:
                    code_result = await self._code_validator.analyze_project(project_id, options)
                    results["code_analysis"] = code_result
                except Exception as e:
                    logger.error(f"TR: Code analysis hatası: {e}")
                    results["code_analysis"] = {"error": str(e)}
            
            # TR: Confidence score hesapla
            confidence_factors = []
            if results["geometry_analysis"].get("valid", False):
                confidence_factors.append(0.5)
            if results["code_analysis"].get("valid", False):
                confidence_factors.append(0.5)
            
            results["confidence_score"] = sum(confidence_factors)
            
            # TR: Öneriler oluştur
            if results["confidence_score"] < 0.7:
                results["recommendations"].append("TR: Proje analizi eksik, daha detaylı inceleme önerilir")
            if not results["geometry_analysis"].get("valid", False):
                results["recommendations"].append("TR: Geometrik validasyon başarısız")
            if not results["code_analysis"].get("valid", False):
                results["recommendations"].append("TR: Kod validasyonu başarısız")
            
            response_data = {
                "success": True,
                "data": results
            }
            
            # TR: Response schema validation
            response_schema_result = await self.validate_json_schema(response_data, "ProjectAnalysisResponse")
            if not response_schema_result["success"]:
                logger.warning(f"TR: Response schema validation başarısız: {response_schema_result['errors']}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"TR: Proje analizi hatası: {e}")
            return {
                "success": False,
                "data": {"error": str(e)}
            }
