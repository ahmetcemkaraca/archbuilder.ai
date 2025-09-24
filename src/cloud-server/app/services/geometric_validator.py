from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import math

logger = logging.getLogger(__name__)


class GeometricValidator:
    """TR: Geometric validation servisi - Revit API entegrasyonu için"""
    
    def __init__(self):
        self._min_room_area = 5.0  # TR: Minimum oda alanı (m²)
        self._max_room_area = 100.0  # TR: Maximum oda alanı (m²)
        self._min_ceiling_height = 2.4  # TR: Minimum tavan yüksekliği (m)
        self._max_ceiling_height = 4.0  # TR: Maximum tavan yüksekliği (m)
    
    async def validate(
        self, 
        payload: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Geometric validation ana fonksiyonu"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "building_type": building_type,
                "validations": {}
            }
            
            # TR: Temel geometri kontrolleri
            if "rooms" in payload:
                room_validation = await self._validate_rooms(payload["rooms"], building_type)
                validation_results["validations"]["rooms"] = room_validation
                if not room_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(room_validation["errors"])
            
            if "dimensions" in payload:
                dimension_validation = await self._validate_dimensions(payload["dimensions"], building_type)
                validation_results["validations"]["dimensions"] = dimension_validation
                if not dimension_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(dimension_validation["errors"])
            
            if "structure" in payload:
                structure_validation = await self._validate_structure(payload["structure"], building_type)
                validation_results["validations"]["structure"] = structure_validation
                if not structure_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(structure_validation["errors"])
            
            # TR: Bina tipine özel kontroller
            building_specific_validation = await self._validate_building_specific(payload, building_type)
            validation_results["validations"]["building_specific"] = building_specific_validation
            if not building_specific_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(building_specific_validation["errors"])
            
            return validation_results
            
        except Exception as e:
            logger.error(f"TR: Geometric validation hatası: {e}")
            return {
                "valid": False,
                "errors": [f"TR: Validation hatası: {str(e)}"],
                "warnings": [],
                "building_type": building_type,
                "validations": {}
            }
    
    async def _validate_rooms(
        self, 
        rooms: List[Dict[str, Any]], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Oda validasyonu"""
        try:
            validation = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "room_count": len(rooms),
                "total_area": 0.0
            }
            
            if not rooms:
                validation["errors"].append("TR: En az bir oda tanımlanmalı")
                validation["valid"] = False
                return validation
            
            for i, room in enumerate(rooms):
                room_validation = await self._validate_single_room(room, i)
                if not room_validation["valid"]:
                    validation["valid"] = False
                    validation["errors"].extend(room_validation["errors"])
                
                validation["warnings"].extend(room_validation["warnings"])
                
                # TR: Alan hesapla
                if "area" in room:
                    validation["total_area"] += float(room["area"])
                elif "length" in room and "width" in room:
                    validation["total_area"] += float(room["length"]) * float(room["width"])
            
            # TR: Toplam alan kontrolü
            if building_type == "residential":
                if validation["total_area"] < 30.0:
                    validation["warnings"].append("TR: Konut için toplam alan çok küçük (30m² altı)")
                elif validation["total_area"] > 300.0:
                    validation["warnings"].append("TR: Konut için toplam alan çok büyük (300m² üstü)")
            
            return validation
            
        except Exception as e:
            logger.error(f"TR: Oda validation hatası: {e}")
            return {
                "valid": False,
                "errors": [f"TR: Oda validation hatası: {str(e)}"],
                "warnings": [],
                "room_count": 0,
                "total_area": 0.0
            }
    
    async def _validate_single_room(
        self, 
        room: Dict[str, Any], 
        room_index: int
    ) -> Dict[str, Any]:
        """TR: Tek oda validasyonu"""
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
            if area < self._min_room_area:
                validation["errors"].append(f"TR: Oda {room_index}: Alan çok küçük ({area}m² < {self._min_room_area}m²)")
                validation["valid"] = False
            elif area > self._max_room_area:
                validation["warnings"].append(f"TR: Oda {room_index}: Alan çok büyük ({area}m² > {self._max_room_area}m²)")
        
        # TR: Boyut kontrolü
        if "length" in room and "width" in room:
            length = float(room["length"])
            width = float(room["width"])
            
            if length <= 0 or width <= 0:
                validation["errors"].append(f"TR: Oda {room_index}: Geçersiz boyutlar (uzunluk: {length}, genişlik: {width})")
                validation["valid"] = False
            
            # TR: En-boy oranı kontrolü
            if length > 0 and width > 0:
                ratio = max(length, width) / min(length, width)
                if ratio > 3.0:
                    validation["warnings"].append(f"TR: Oda {room_index}: En-boy oranı çok yüksek ({ratio:.1f})")
        
        # TR: Yükseklik kontrolü
        if "height" in room:
            height = float(room["height"])
            if height < self._min_ceiling_height:
                validation["errors"].append(f"TR: Oda {room_index}: Tavan yüksekliği çok düşük ({height}m < {self._min_ceiling_height}m)")
                validation["valid"] = False
            elif height > self._max_ceiling_height:
                validation["warnings"].append(f"TR: Oda {room_index}: Tavan yüksekliği çok yüksek ({height}m > {self._max_ceiling_height}m)")
        
        return validation
    
    async def _validate_dimensions(
        self, 
        dimensions: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Boyut validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # TR: Temel boyut kontrolleri
        if "total_area" in dimensions:
            total_area = float(dimensions["total_area"])
            if total_area <= 0:
                validation["errors"].append("TR: Toplam alan pozitif olmalı")
                validation["valid"] = False
        
        if "height" in dimensions:
            height = float(dimensions["height"])
            if height < self._min_ceiling_height:
                validation["errors"].append(f"TR: Yükseklik çok düşük ({height}m < {self._min_ceiling_height}m)")
                validation["valid"] = False
        
        return validation
    
    async def _validate_structure(
        self, 
        structure: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Yapı validasyonu"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # TR: Yapı tipi kontrolü
        if "type" in structure:
            valid_types = ["concrete", "steel", "wood", "masonry"]
            if structure["type"] not in valid_types:
                validation["errors"].append(f"TR: Geçersiz yapı tipi: {structure['type']}")
                validation["valid"] = False
        
        # TR: Kat sayısı kontrolü
        if "floors" in structure:
            floors = int(structure["floors"])
            if floors <= 0:
                validation["errors"].append("TR: Kat sayısı pozitif olmalı")
                validation["valid"] = False
            elif floors > 50:
                validation["warnings"].append("TR: Kat sayısı çok yüksek (50 üstü)")
        
        return validation
    
    async def _validate_building_specific(
        self, 
        payload: Dict[str, Any], 
        building_type: str
    ) -> Dict[str, Any]:
        """TR: Bina tipine özel validasyon"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if building_type == "residential":
            # TR: Konut özel kontrolleri
            if "rooms" in payload:
                rooms = payload["rooms"]
                bedroom_count = sum(1 for room in rooms if room.get("type") == "bedroom")
                if bedroom_count == 0:
                    validation["warnings"].append("TR: Konut için yatak odası bulunamadı")
                
                bathroom_count = sum(1 for room in rooms if room.get("type") == "bathroom")
                if bathroom_count == 0:
                    validation["errors"].append("TR: Konut için banyo bulunamadı")
                    validation["valid"] = False
        
        elif building_type == "commercial":
            # TR: Ticari yapı özel kontrolleri
            if "rooms" in payload:
                rooms = payload["rooms"]
                office_count = sum(1 for room in rooms if room.get("type") == "office")
                if office_count == 0:
                    validation["warnings"].append("TR: Ticari yapı için ofis alanı bulunamadı")
        
        return validation
    
    async def analyze_project(
        self, 
        project_id: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """TR: Proje analizi - geometric aspects"""
        try:
            if options is None:
                options = {}
            
            # TR: Mock analiz sonuçları - gerçek implementasyonda Revit API'dan veri çekilecek
            analysis = {
                "project_id": project_id,
                "valid": True,
                "geometry_summary": {
                    "total_rooms": 0,
                    "total_area": 0.0,
                    "floor_count": 0,
                    "structure_type": "unknown"
                },
                "issues": [],
                "recommendations": [],
                "confidence_score": 0.8
            }
            
            # TR: Burada Revit API'dan gerçek proje verilerini çekeceğiz
            # Şimdilik mock veri döndürüyoruz
            
            return analysis
            
        except Exception as e:
            logger.error(f"TR: Proje analizi hatası: {e}")
            return {
                "project_id": project_id,
                "valid": False,
                "geometry_summary": {},
                "issues": [f"TR: Analiz hatası: {str(e)}"],
                "recommendations": [],
                "confidence_score": 0.0
            }
