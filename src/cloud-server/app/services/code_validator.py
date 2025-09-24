from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeValidator:
    """TR: Building code validation servisi - regional building codes için"""
    
    def __init__(self):
        # TR: Regional building codes - şimdilik mock veriler
        self._building_codes = {
            "TR": {
                "residential": {
                    "min_room_area": 5.0,
                    "max_room_area": 100.0,
                    "min_ceiling_height": 2.4,
                    "min_window_area_ratio": 0.1,
                    "required_rooms": ["bedroom", "bathroom", "kitchen"],
                    "fire_safety_requirements": True,
                    "accessibility_requirements": True
                },
                "commercial": {
                    "min_room_area": 10.0,
                    "max_room_area": 500.0,
                    "min_ceiling_height": 2.7,
                    "min_window_area_ratio": 0.15,
                    "required_rooms": ["office", "restroom"],
                    "fire_safety_requirements": True,
                    "accessibility_requirements": True
                }
            },
            "US": {
                "residential": {
                    "min_room_area": 70.0,  # TR: feet²
                    "max_room_area": 1000.0,
                    "min_ceiling_height": 8.0,  # TR: feet
                    "min_window_area_ratio": 0.1,
                    "required_rooms": ["bedroom", "bathroom", "kitchen"],
                    "fire_safety_requirements": True,
                    "accessibility_requirements": True
                },
                "commercial": {
                    "min_room_area": 120.0,
                    "max_room_area": 5000.0,
                    "min_ceiling_height": 9.0,
                    "min_window_area_ratio": 0.15,
                    "required_rooms": ["office", "restroom"],
                    "fire_safety_requirements": True,
                    "accessibility_requirements": True
                }
            }
        }
    
    async def validate(
        self, 
        payload: Dict[str, Any], 
        building_type: str,
        region: str = "TR"
    ) -> Dict[str, Any]:
        """TR: Building code validation ana fonksiyonu"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "building_type": building_type,
                "region": region,
                "code_compliance": {},
                "validations": {}
            }
            
            # TR: Regional code kontrolü
            if region not in self._building_codes:
                validation_results["errors"].append(f"TR: Desteklenmeyen bölge: {region}")
                validation_results["valid"] = False
                return validation_results
            
            if building_type not in self._building_codes[region]:
                validation_results["errors"].append(f"TR: Desteklenmeyen bina tipi: {building_type}")
                validation_results["valid"] = False
                return validation_results
            
            code_requirements = self._building_codes[region][building_type]
            
            # TR: Oda alanı kontrolleri
            if "rooms" in payload:
                room_validation = await self._validate_room_requirements(
                    payload["rooms"], code_requirements
                )
                validation_results["validations"]["rooms"] = room_validation
                if not room_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(room_validation["errors"])
            
            # TR: Yükseklik kontrolleri
            if "dimensions" in payload:
                height_validation = await self._validate_height_requirements(
                    payload["dimensions"], code_requirements
                )
                validation_results["validations"]["height"] = height_validation
                if not height_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(height_validation["errors"])
            
            # TR: Yangın güvenliği kontrolleri
            fire_safety_validation = await self._validate_fire_safety(
                payload, code_requirements
            )
            validation_results["validations"]["fire_safety"] = fire_safety_validation
            if not fire_safety_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(fire_safety_validation["errors"])
            
            # TR: Erişilebilirlik kontrolleri
            accessibility_validation = await self._validate_accessibility(
                payload, code_requirements
            )
            validation_results["validations"]["accessibility"] = accessibility_validation
            if not accessibility_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(accessibility_validation["errors"])
            
            # TR: Code compliance özeti
            validation_results["code_compliance"] = {
                "region": region,
                "building_type": building_type,
                "compliance_score": self._calculate_compliance_score(validation_results["validations"]),
                "requirements_met": self._count_requirements_met(validation_results["validations"])
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"TR: Code validation hatası: {e}")
            return {
                "valid": False,
                "errors": [f"TR: Validation hatası: {str(e)}"],
                "warnings": [],
                "building_type": building_type,
                "region": region,
                "code_compliance": {},
                "validations": {}
            }
    
    async def _validate_room_requirements(
        self, 
        rooms: List[Dict[str, Any]], 
        code_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TR: Oda gereksinimleri validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "room_compliance": {}
        }
        
        # TR: Gerekli oda tiplerini kontrol et
        required_rooms = code_requirements.get("required_rooms", [])
        room_types = [room.get("type", "unknown") for room in rooms]
        
        for required_room in required_rooms:
            if required_room not in room_types:
                validation["errors"].append(f"TR: Gerekli oda tipi bulunamadı: {required_room}")
                validation["valid"] = False
        
        # TR: Her oda için alan kontrolü
        for i, room in enumerate(rooms):
            room_validation = await self._validate_room_compliance(room, code_requirements, i)
            validation["room_compliance"][f"room_{i}"] = room_validation
            
            if not room_validation["valid"]:
                validation["valid"] = False
                validation["errors"].extend(room_validation["errors"])
            
            validation["warnings"].extend(room_validation["warnings"])
        
        return validation
    
    async def _validate_room_compliance(
        self, 
        room: Dict[str, Any], 
        code_requirements: Dict[str, Any], 
        room_index: int
    ) -> Dict[str, Any]:
        """TR: Tek oda compliance kontrolü"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # TR: Alan kontrolü
        area = None
        if "area" in room:
            area = float(room["area"])
        elif "length" in room and "width" in room:
            area = float(room["length"]) * float(room["width"])
        
        if area is not None:
            min_area = code_requirements.get("min_room_area", 5.0)
            max_area = code_requirements.get("max_room_area", 100.0)
            
            if area < min_area:
                validation["errors"].append(
                    f"TR: Oda {room_index}: Minimum alan gereksinimi karşılanmıyor "
                    f"({area}m² < {min_area}m²)"
                )
                validation["valid"] = False
            elif area > max_area:
                validation["warnings"].append(
                    f"TR: Oda {room_index}: Maksimum alan aşılıyor "
                    f"({area}m² > {max_area}m²)"
                )
        
        # TR: Pencere alanı kontrolü
        if "window_area" in room and "area" in room:
            window_ratio = float(room["window_area"]) / float(room["area"])
            min_window_ratio = code_requirements.get("min_window_area_ratio", 0.1)
            
            if window_ratio < min_window_ratio:
                validation["errors"].append(
                    f"TR: Oda {room_index}: Pencere alanı yetersiz "
                    f"({window_ratio:.2%} < {min_window_ratio:.2%})"
                )
                validation["valid"] = False
        
        return validation
    
    async def _validate_height_requirements(
        self, 
        dimensions: Dict[str, Any], 
        code_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TR: Yükseklik gereksinimleri validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if "height" in dimensions:
            height = float(dimensions["height"])
            min_height = code_requirements.get("min_ceiling_height", 2.4)
            
            if height < min_height:
                validation["errors"].append(
                    f"TR: Minimum tavan yüksekliği karşılanmıyor "
                    f"({height}m < {min_height}m)"
                )
                validation["valid"] = False
        
        return validation
    
    async def _validate_fire_safety(
        self, 
        payload: Dict[str, Any], 
        code_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TR: Yangın güvenliği validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not code_requirements.get("fire_safety_requirements", False):
            return validation
        
        # TR: Yangın güvenliği kontrolleri
        fire_safety_checks = []
        
        # TR: Kaçış yolları kontrolü
        if "escape_routes" not in payload:
            fire_safety_checks.append("TR: Kaçış yolları tanımlanmamış")
        
        # TR: Yangın alarmı kontrolü
        if "fire_alarm" not in payload:
            fire_safety_checks.append("TR: Yangın alarm sistemi belirtilmemiş")
        
        # TR: Yangın söndürücü kontrolü
        if "fire_extinguishers" not in payload:
            fire_safety_checks.append("TR: Yangın söndürücü belirtilmemiş")
        
        if fire_safety_checks:
            validation["warnings"].extend(fire_safety_checks)
            # TR: Yangın güvenliği kritik değil, sadece uyarı
        
        return validation
    
    async def _validate_accessibility(
        self, 
        payload: Dict[str, Any], 
        code_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """TR: Erişilebilirlik validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not code_requirements.get("accessibility_requirements", False):
            return validation
        
        # TR: Erişilebilirlik kontrolleri
        accessibility_checks = []
        
        # TR: Ramp kontrolü
        if "ramps" not in payload:
            accessibility_checks.append("TR: Ramp erişimi belirtilmemiş")
        
        # TR: Asansör kontrolü
        if "elevator" not in payload:
            accessibility_checks.append("TR: Asansör erişimi belirtilmemiş")
        
        # TR: Geniş kapılar kontrolü
        if "doors" in payload:
            doors = payload["doors"]
            narrow_doors = [d for d in doors if d.get("width", 0) < 0.9]
            if narrow_doors:
                accessibility_checks.append("TR: Bazı kapılar tekerlekli sandalye için çok dar")
        
        if accessibility_checks:
            validation["warnings"].extend(accessibility_checks)
            # TR: Erişilebilirlik kritik değil, sadece uyarı
        
        return validation
    
    def _calculate_compliance_score(self, validations: Dict[str, Any]) -> float:
        """TR: Compliance score hesapla"""
        if not validations:
            return 0.0
        
        valid_count = sum(1 for validation in validations.values() if validation.get("valid", False))
        total_count = len(validations)
        
        return valid_count / total_count if total_count > 0 else 0.0
    
    def _count_requirements_met(self, validations: Dict[str, Any]) -> int:
        """TR: Karşılanan gereksinim sayısı"""
        return sum(1 for validation in validations.values() if validation.get("valid", False))
    
    async def analyze_project(
        self, 
        project_id: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """TR: Proje analizi - code compliance aspects"""
        try:
            if options is None:
                options = {}
            
            region = options.get("region", "TR")
            
            # TR: Mock analiz sonuçları - gerçek implementasyonda regional codes'dan veri çekilecek
            analysis = {
                "project_id": project_id,
                "valid": True,
                "code_compliance": {
                    "region": region,
                    "compliance_score": 0.85,
                    "requirements_met": 8,
                    "total_requirements": 10,
                    "critical_violations": 0,
                    "warnings": 2
                },
                "issues": [],
                "recommendations": [
                    "TR: Yangın güvenliği sistemi eklenmeli",
                    "TR: Erişilebilirlik önlemleri gözden geçirilmeli"
                ],
                "confidence_score": 0.8
            }
            
            # TR: Burada gerçek regional building codes veritabanından analiz yapılacak
            # Şimdilik mock veri döndürüyoruz
            
            return analysis
            
        except Exception as e:
            logger.error(f"TR: Proje code analizi hatası: {e}")
            return {
                "project_id": project_id,
                "valid": False,
                "code_compliance": {},
                "issues": [f"TR: Analiz hatası: {str(e)}"],
                "recommendations": [],
                "confidence_score": 0.0
            }
