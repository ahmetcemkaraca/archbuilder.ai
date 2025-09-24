from __future__ import annotations

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RegionalConfigService:
    """TR: Regional configuration ve i18n servisi - P15-T3, P25-T1, P25-T2, P25-T3"""
    
    def __init__(self):
        self._configs = {}
        self._i18n_data = {}
        self._load_regional_configs()
        self._load_i18n_data()
    
    def _load_regional_configs(self) -> None:
        """TR: Regional configuration'ları yükle - P25-T2"""
        try:
            self._configs = {
                "TR": {
                    "country_code": "TR",
                    "language": "tr",
                    "currency": "TRY",
                    "timezone": "Europe/Istanbul",
                    "building_codes": {
                        "residential": {
                            "min_room_area": 5.0,
                            "max_room_area": 100.0,
                            "min_ceiling_height": 2.4,
                            "min_window_area_ratio": 0.1,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        },
                        "commercial": {
                            "min_room_area": 10.0,
                            "max_room_area": 500.0,
                            "min_ceiling_height": 2.7,
                            "min_window_area_ratio": 0.15,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        }
                    },
                    "units": {
                        "length": "meter",
                        "area": "square_meter",
                        "volume": "cubic_meter",
                        "temperature": "celsius"
                    },
                    "date_format": "%d.%m.%Y",
                    "number_format": {
                        "decimal_separator": ",",
                        "thousands_separator": ".",
                        "decimal_places": 2
                    }
                },
                "US": {
                    "country_code": "US",
                    "language": "en",
                    "currency": "USD",
                    "timezone": "America/New_York",
                    "building_codes": {
                        "residential": {
                            "min_room_area": 70.0,  # TR: feet²
                            "max_room_area": 1000.0,
                            "min_ceiling_height": 8.0,  # TR: feet
                            "min_window_area_ratio": 0.1,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        },
                        "commercial": {
                            "min_room_area": 120.0,
                            "max_room_area": 5000.0,
                            "min_ceiling_height": 9.0,
                            "min_window_area_ratio": 0.15,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        }
                    },
                    "units": {
                        "length": "feet",
                        "area": "square_feet",
                        "volume": "cubic_feet",
                        "temperature": "fahrenheit"
                    },
                    "date_format": "%m/%d/%Y",
                    "number_format": {
                        "decimal_separator": ".",
                        "thousands_separator": ",",
                        "decimal_places": 2
                    }
                },
                "EU": {
                    "country_code": "EU",
                    "language": "en",
                    "currency": "EUR",
                    "timezone": "Europe/Brussels",
                    "building_codes": {
                        "residential": {
                            "min_room_area": 8.0,
                            "max_room_area": 150.0,
                            "min_ceiling_height": 2.5,
                            "min_window_area_ratio": 0.12,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        },
                        "commercial": {
                            "min_room_area": 12.0,
                            "max_room_area": 800.0,
                            "min_ceiling_height": 2.8,
                            "min_window_area_ratio": 0.18,
                            "fire_safety_required": True,
                            "accessibility_required": True
                        }
                    },
                    "units": {
                        "length": "meter",
                        "area": "square_meter",
                        "volume": "cubic_meter",
                        "temperature": "celsius"
                    },
                    "date_format": "%d/%m/%Y",
                    "number_format": {
                        "decimal_separator": ",",
                        "thousands_separator": " ",
                        "decimal_places": 2
                    }
                }
            }
            
            logger.info(f"TR: {len(self._configs)} regional config yüklendi")
            
        except Exception as e:
            logger.error(f"TR: Regional config yükleme hatası: {e}")
            self._configs = {}
    
    def _load_i18n_data(self) -> None:
        """TR: i18n verilerini yükle - P25-T3"""
        try:
            self._i18n_data = {
                "tr": {
                    "common": {
                        "save": "Kaydet",
                        "cancel": "İptal",
                        "delete": "Sil",
                        "edit": "Düzenle",
                        "create": "Oluştur",
                        "search": "Ara",
                        "filter": "Filtrele",
                        "sort": "Sırala",
                        "loading": "Yükleniyor...",
                        "error": "Hata",
                        "success": "Başarılı",
                        "warning": "Uyarı",
                        "info": "Bilgi"
                    },
                    "building_types": {
                        "residential": "Konut",
                        "commercial": "Ticari",
                        "industrial": "Endüstriyel",
                        "public": "Kamu",
                        "mixed_use": "Karma Kullanım"
                    },
                    "room_types": {
                        "bedroom": "Yatak Odası",
                        "bathroom": "Banyo",
                        "kitchen": "Mutfak",
                        "living_room": "Oturma Odası",
                        "office": "Ofis",
                        "meeting_room": "Toplantı Odası",
                        "corridor": "Koridor",
                        "staircase": "Merdiven"
                    },
                    "validation": {
                        "area_too_small": "Alan çok küçük",
                        "area_too_large": "Alan çok büyük",
                        "height_too_low": "Yükseklik çok düşük",
                        "height_too_high": "Yükseklik çok yüksek",
                        "window_area_insufficient": "Pencere alanı yetersiz",
                        "fire_safety_required": "Yangın güvenliği gerekli",
                        "accessibility_required": "Erişilebilirlik gerekli"
                    },
                    "analysis": {
                        "geometry_analysis": "Geometri Analizi",
                        "code_analysis": "Kod Analizi",
                        "recommendations": "Öneriler",
                        "confidence_score": "Güven Skoru",
                        "compliance_score": "Uyum Skoru"
                    }
                },
                "en": {
                    "common": {
                        "save": "Save",
                        "cancel": "Cancel",
                        "delete": "Delete",
                        "edit": "Edit",
                        "create": "Create",
                        "search": "Search",
                        "filter": "Filter",
                        "sort": "Sort",
                        "loading": "Loading...",
                        "error": "Error",
                        "success": "Success",
                        "warning": "Warning",
                        "info": "Info"
                    },
                    "building_types": {
                        "residential": "Residential",
                        "commercial": "Commercial",
                        "industrial": "Industrial",
                        "public": "Public",
                        "mixed_use": "Mixed Use"
                    },
                    "room_types": {
                        "bedroom": "Bedroom",
                        "bathroom": "Bathroom",
                        "kitchen": "Kitchen",
                        "living_room": "Living Room",
                        "office": "Office",
                        "meeting_room": "Meeting Room",
                        "corridor": "Corridor",
                        "staircase": "Staircase"
                    },
                    "validation": {
                        "area_too_small": "Area too small",
                        "area_too_large": "Area too large",
                        "height_too_low": "Height too low",
                        "height_too_high": "Height too high",
                        "window_area_insufficient": "Window area insufficient",
                        "fire_safety_required": "Fire safety required",
                        "accessibility_required": "Accessibility required"
                    },
                    "analysis": {
                        "geometry_analysis": "Geometry Analysis",
                        "code_analysis": "Code Analysis",
                        "recommendations": "Recommendations",
                        "confidence_score": "Confidence Score",
                        "compliance_score": "Compliance Score"
                    }
                }
            }
            
            logger.info(f"TR: {len(self._i18n_data)} dil desteği yüklendi")
            
        except Exception as e:
            logger.error(f"TR: i18n data yükleme hatası: {e}")
            self._i18n_data = {}
    
    def get_regional_config(self, region: str) -> Dict[str, Any]:
        """TR: Regional config getir - P25-T2"""
        try:
            if region not in self._configs:
                logger.warning(f"TR: Bilinmeyen bölge: {region}, varsayılan TR kullanılıyor")
                region = "TR"
            
            return self._configs.get(region, {})
            
        except Exception as e:
            logger.error(f"TR: Regional config getirme hatası: {e}")
            return {}
    
    def get_building_codes(self, region: str, building_type: str) -> Dict[str, Any]:
        """TR: Building codes getir - P25-T1"""
        try:
            config = self.get_regional_config(region)
            building_codes = config.get("building_codes", {})
            
            if building_type not in building_codes:
                logger.warning(f"TR: Bilinmeyen bina tipi: {building_type}")
                return {}
            
            return building_codes[building_type]
            
        except Exception as e:
            logger.error(f"TR: Building codes getirme hatası: {e}")
            return {}
    
    def get_units(self, region: str) -> Dict[str, str]:
        """TR: Birim sistemini getir"""
        try:
            config = self.get_regional_config(region)
            return config.get("units", {})
            
        except Exception as e:
            logger.error(f"TR: Units getirme hatası: {e}")
            return {}
    
    def format_number(self, value: float, region: str) -> str:
        """TR: Sayıyı regional format'a çevir"""
        try:
            config = self.get_regional_config(region)
            number_format = config.get("number_format", {})
            
            decimal_separator = number_format.get("decimal_separator", ".")
            thousands_separator = number_format.get("thousands_separator", ",")
            decimal_places = number_format.get("decimal_places", 2)
            
            # TR: Basit formatting
            formatted = f"{value:,.{decimal_places}f}"
            formatted = formatted.replace(",", "TEMP_THOUSANDS")
            formatted = formatted.replace(".", decimal_separator)
            formatted = formatted.replace("TEMP_THOUSANDS", thousands_separator)
            
            return formatted
            
        except Exception as e:
            logger.error(f"TR: Number formatting hatası: {e}")
            return str(value)
    
    def format_date(self, date: datetime, region: str) -> str:
        """TR: Tarihi regional format'a çevir"""
        try:
            config = self.get_regional_config(region)
            date_format = config.get("date_format", "%d.%m.%Y")
            
            return date.strftime(date_format)
            
        except Exception as e:
            logger.error(f"TR: Date formatting hatası: {e}")
            return date.isoformat()
    
    def get_translation(self, key: str, language: str = "tr") -> str:
        """TR: Çeviri getir - P25-T3"""
        try:
            if language not in self._i18n_data:
                logger.warning(f"TR: Desteklenmeyen dil: {language}, varsayılan tr kullanılıyor")
                language = "tr"
            
            # TR: Nested key desteği (örn: "common.save")
            keys = key.split(".")
            value = self._i18n_data[language]
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    logger.warning(f"TR: Çeviri bulunamadı: {key} ({language})")
                    return key  # TR: Key'i geri döndür
            
            return str(value)
            
        except Exception as e:
            logger.error(f"TR: Translation getirme hatası: {e}")
            return key
    
    def get_available_regions(self) -> List[str]:
        """TR: Mevcut bölgeleri listele"""
        return list(self._configs.keys())
    
    def get_available_languages(self) -> List[str]:
        """TR: Mevcut dilleri listele"""
        return list(self._i18n_data.keys())
    
    def get_building_types(self, region: str) -> List[str]:
        """TR: Bina tiplerini listele"""
        try:
            config = self.get_regional_config(region)
            building_codes = config.get("building_codes", {})
            return list(building_codes.keys())
            
        except Exception as e:
            logger.error(f"TR: Building types getirme hatası: {e}")
            return []
    
    def validate_region_building_type(self, region: str, building_type: str) -> bool:
        """TR: Region ve building type kombinasyonunu validate et"""
        try:
            building_types = self.get_building_types(region)
            return building_type in building_types
            
        except Exception as e:
            logger.error(f"TR: Region/building type validation hatası: {e}")
            return False
    
    def get_localized_building_type(self, building_type: str, language: str = "tr") -> str:
        """TR: Bina tipini localize et"""
        try:
            return self.get_translation(f"building_types.{building_type}", language)
            
        except Exception as e:
            logger.error(f"TR: Building type localization hatası: {e}")
            return building_type
    
    def get_localized_room_type(self, room_type: str, language: str = "tr") -> str:
        """TR: Oda tipini localize et"""
        try:
            return self.get_translation(f"room_types.{room_type}", language)
            
        except Exception as e:
            logger.error(f"TR: Room type localization hatası: {e}")
            return room_type
    
    def get_localized_validation_message(self, message_key: str, language: str = "tr") -> str:
        """TR: Validation mesajını localize et"""
        try:
            return self.get_translation(f"validation.{message_key}", language)
            
        except Exception as e:
            logger.error(f"TR: Validation message localization hatası: {e}")
            return message_key
    
    def get_localized_analysis_label(self, label_key: str, language: str = "tr") -> str:
        """TR: Analysis label'ını localize et"""
        try:
            return self.get_translation(f"analysis.{label_key}", language)
            
        except Exception as e:
            logger.error(f"TR: Analysis label localization hatası: {e}")
            return label_key
