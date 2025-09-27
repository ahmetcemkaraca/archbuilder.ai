from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BuildingCodeStandard(Enum):
    """TR: Desteklenen yapı yönetmeliği standartları"""

    TURKISH_BUILDING_CODE = "TBC"  # TR: Türk İmar Yönetmeliği
    INTERNATIONAL_BUILDING_CODE = "IBC"  # TR: Amerikan IBC
    EUROCODE = "EC"  # TR: Avrupa Standardı
    CANADIAN_BUILDING_CODE = "CBC"  # TR: Kanada Yapı Yönetmeliği
    AUSTRALIAN_BUILDING_CODE = "ABC"  # TR: Avustralya BCA
    BRITISH_BUILDING_REGULATIONS = "BBR"  # TR: İngiliz Building Regulations
    GERMAN_DIN = "DIN"  # TR: Alman DIN Standartları
    FRENCH_REGULATIONS = "FR_REG"  # TR: Fransız Regulations
    JAPANESE_BUILDING_STANDARD = "JBS"  # TR: Japon Building Standard Law
    SINGAPORE_BUILDING_CODE = "SBC"  # TR: Singapur Building Code


@dataclass
class BuildingCodeRequirement:
    """TR: Yapı yönetmeliği gereksinimi"""

    code: str
    name: str
    description: str
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    unit: Optional[str] = None
    mandatory: bool = True
    building_types: Optional[List[str]] = None
    floor_types: Optional[List[str]] = None
    source_article: Optional[str] = None

    def __post_init__(self):
        if self.building_types is None:
            self.building_types = ["all"]
        if self.floor_types is None:
            self.floor_types = ["all"]


class RegionalBuildingCodesService:
    """TR: Bölgesel yapı yönetmelikleri veritabanı servisi"""

    def __init__(self):
        self._building_codes: Dict[str, Dict[str, List[BuildingCodeRequirement]]] = {}
        self._load_building_codes_database()

    def _load_building_codes_database(self) -> None:
        """TR: Yapı yönetmelikleri veritabanını yükle"""
        try:
            # TR: Türk İmar Yönetmeliği
            turkish_codes = self._load_turkish_building_codes()
            self._building_codes["TR"] = turkish_codes

            # TR: Amerikan IBC
            us_codes = self._load_us_building_codes()
            self._building_codes["US"] = us_codes

            # TR: Avrupa Eurocode
            eu_codes = self._load_eu_building_codes()
            self._building_codes["EU"] = eu_codes

            # TR: Kanada CBC
            ca_codes = self._load_canadian_building_codes()
            self._building_codes["CA"] = ca_codes

            # TR: Asya-Pasifik (Singapur temelinde)
            apac_codes = self._load_apac_building_codes()
            self._building_codes["APAC"] = apac_codes

            # TR: Brezilya ABNT
            br_codes = self._load_brazilian_building_codes()
            self._building_codes["BR"] = br_codes

            logger.info(
                f"TR: {len(self._building_codes)} bölge için yapı yönetmelikleri yüklendi"
            )

        except Exception as e:
            logger.error(f"TR: Building codes veritabanı yükleme hatası: {e}")
            self._building_codes = {}

    def _load_turkish_building_codes(self) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Türk İmar Yönetmeliği kodlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="TR_RES_001",
                    name="Minimum Oda Alanı",
                    description="Konut yatak odası minimum alanı",
                    min_value=9.0,
                    unit="m²",
                    building_types=["residential"],
                    source_article="İmar Yönetmeliği Madde 15",
                ),
                BuildingCodeRequirement(
                    code="TR_RES_002",
                    name="Minimum Tavan Yüksekliği",
                    description="Konut odaları minimum tavan yüksekliği",
                    min_value=2.40,
                    unit="m",
                    building_types=["residential"],
                    source_article="İmar Yönetmeliği Madde 15",
                ),
                BuildingCodeRequirement(
                    code="TR_RES_003",
                    name="Pencere Alanı Oranı",
                    description="Oda alanına göre minimum pencere alanı oranı",
                    min_value=0.125,  # TR: 1/8 oranı
                    unit="ratio",
                    building_types=["residential"],
                    source_article="İmar Yönetmeliği Madde 16",
                ),
                BuildingCodeRequirement(
                    code="TR_RES_004",
                    name="Havalandırma Açıklığı",
                    description="Doğal havalandırma için açılabilir pencere alanı",
                    min_value=0.05,  # TR: 1/20 oranı
                    unit="ratio",
                    building_types=["residential"],
                    source_article="İmar Yönetmeliği Madde 16",
                ),
                BuildingCodeRequirement(
                    code="TR_RES_005",
                    name="Kaçış Mesafesi",
                    description="Yangın çıkışına maksimum uzaklık",
                    max_value=30.0,
                    unit="m",
                    building_types=["residential"],
                    source_article="Yangın Güvenliği Yönetmeliği",
                ),
            ],
            "commercial": [
                BuildingCodeRequirement(
                    code="TR_COM_001",
                    name="Minimum Tavan Yüksekliği",
                    description="Ticari alanlar minimum tavan yüksekliği",
                    min_value=2.70,
                    unit="m",
                    building_types=["commercial"],
                    source_article="İmar Yönetmeliği Madde 18",
                ),
                BuildingCodeRequirement(
                    code="TR_COM_002",
                    name="Engelli Erişimi",
                    description="Engelli erişim kapı genişliği",
                    min_value=0.90,
                    unit="m",
                    building_types=["commercial"],
                    source_article="Erişilebilirlik Yönetmeliği",
                ),
                BuildingCodeRequirement(
                    code="TR_COM_003",
                    name="TAKS Oranı",
                    description="İmar adasında bina kapladığı alan oranı",
                    max_value=0.40,
                    unit="ratio",
                    building_types=["commercial"],
                    source_article="İmar Planı Şartları",
                ),
            ],
        }

    def _load_us_building_codes(self) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Amerikan IBC kodlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="IBC_RES_001",
                    name="Minimum Room Area",
                    description="Minimum habitable room area",
                    min_value=70.0,
                    unit="sq ft",
                    building_types=["residential"],
                    source_article="IBC Section 1208.2",
                ),
                BuildingCodeRequirement(
                    code="IBC_RES_002",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height for habitable rooms",
                    min_value=7.5,
                    unit="ft",
                    building_types=["residential"],
                    source_article="IBC Section 1208.2",
                ),
                BuildingCodeRequirement(
                    code="IBC_RES_003",
                    name="Window Area Ratio",
                    description="Minimum window area to floor area ratio",
                    min_value=0.10,
                    unit="ratio",
                    building_types=["residential"],
                    source_article="IBC Section 1205.2",
                ),
            ],
            "commercial": [
                BuildingCodeRequirement(
                    code="IBC_COM_001",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height for commercial spaces",
                    min_value=8.0,
                    unit="ft",
                    building_types=["commercial"],
                    source_article="IBC Section 1003.2",
                ),
                BuildingCodeRequirement(
                    code="IBC_COM_002",
                    name="ADA Door Width",
                    description="ADA compliant door width",
                    min_value=32.0,
                    unit="inches",
                    building_types=["commercial"],
                    source_article="ADA Standards Section 404.2.3",
                ),
            ],
        }

    def _load_eu_building_codes(self) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Avrupa Eurocode standartlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="EC_RES_001",
                    name="Minimum Room Area",
                    description="Minimum habitable room area (EU average)",
                    min_value=8.0,
                    unit="m²",
                    building_types=["residential"],
                    source_article="EN 15251",
                ),
                BuildingCodeRequirement(
                    code="EC_RES_002",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height for residential",
                    min_value=2.50,
                    unit="m",
                    building_types=["residential"],
                    source_article="EN 15251",
                ),
                BuildingCodeRequirement(
                    code="EC_RES_003",
                    name="Energy Performance",
                    description="Maximum annual energy consumption",
                    max_value=100.0,
                    unit="kWh/m²/year",
                    building_types=["residential"],
                    source_article="EPBD Directive",
                ),
            ],
            "commercial": [
                BuildingCodeRequirement(
                    code="EC_COM_001",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height for commercial",
                    min_value=2.70,
                    unit="m",
                    building_types=["commercial"],
                    source_article="EN 15251",
                ),
                BuildingCodeRequirement(
                    code="EC_COM_002",
                    name="Accessibility Width",
                    description="Accessible door width",
                    min_value=0.85,
                    unit="m",
                    building_types=["commercial"],
                    source_article="EN 17210",
                ),
            ],
        }

    def _load_canadian_building_codes(self) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Kanada NBC kodlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="NBC_RES_001",
                    name="Minimum Room Area",
                    description="Minimum area for principal rooms",
                    min_value=6.5,
                    unit="m²",
                    building_types=["residential"],
                    source_article="NBC 9.5.2.1",
                ),
                BuildingCodeRequirement(
                    code="NBC_RES_002",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height",
                    min_value=2.30,
                    unit="m",
                    building_types=["residential"],
                    source_article="NBC 9.5.3.1",
                ),
            ]
        }

    def _load_apac_building_codes(self) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Asya-Pasifik (Singapur temelinde) kodlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="SBC_RES_001",
                    name="Minimum Room Area",
                    description="Minimum habitable room area",
                    min_value=6.0,
                    unit="m²",
                    building_types=["residential"],
                    source_article="Singapore Building Code",
                ),
                BuildingCodeRequirement(
                    code="SBC_RES_002",
                    name="Minimum Ceiling Height",
                    description="Minimum ceiling height",
                    min_value=2.60,
                    unit="m",
                    building_types=["residential"],
                    source_article="Singapore Building Code",
                ),
            ]
        }

    def _load_brazilian_building_codes(
        self,
    ) -> Dict[str, List[BuildingCodeRequirement]]:
        """TR: Brezilya ABNT kodlarını yükle"""
        return {
            "residential": [
                BuildingCodeRequirement(
                    code="ABNT_RES_001",
                    name="Área Mínima do Quarto",
                    description="Área mínima para dormitórios",
                    min_value=8.0,
                    unit="m²",
                    building_types=["residential"],
                    source_article="NBR 15575",
                ),
                BuildingCodeRequirement(
                    code="ABNT_RES_002",
                    name="Altura Mínima do Pé-direito",
                    description="Altura mínima do pé-direito",
                    min_value=2.50,
                    unit="m",
                    building_types=["residential"],
                    source_article="NBR 15575",
                ),
            ]
        }

    def get_building_requirements(
        self, region: str, building_type: str
    ) -> List[Dict[str, Any]]:
        """TR: Belirtilen bölge ve bina tipi için yapı gereksinimlerini getir"""
        try:
            region_codes = self._building_codes.get(region.upper(), {})
            requirements = region_codes.get(building_type.lower(), [])

            result = []
            for req in requirements:
                result.append(
                    {
                        "code": req.code,
                        "name": req.name,
                        "description": req.description,
                        "min_value": req.min_value,
                        "max_value": req.max_value,
                        "unit": req.unit,
                        "mandatory": req.mandatory,
                        "building_types": req.building_types,
                        "source_article": req.source_article,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"TR: Building requirements getirme hatası: {e}")
            return []

    def validate_design_against_codes(
        self, design_params: Dict[str, Any], region: str, building_type: str
    ) -> Dict[str, Any]:
        """TR: Tasarımı yapı yönetmeliklerine göre doğrula"""
        try:
            requirements = self.get_building_requirements(region, building_type)
            validation_results = {
                "region": region,
                "building_type": building_type,
                "compliant": True,
                "violations": [],
                "warnings": [],
                "recommendations": [],
                "validated_requirements": [],
            }

            for req_dict in requirements:
                req_code = req_dict["code"]
                req_name = req_dict["name"]
                min_val = req_dict.get("min_value")
                max_val = req_dict.get("max_value")
                unit = req_dict.get("unit", "")
                mandatory = req_dict.get("mandatory", True)

                # TR: Design parametresini bul
                design_value = self._extract_design_value(
                    design_params, req_code, req_dict
                )

                if design_value is not None:
                    violation = None

                    # TR: Minimum değer kontrolü
                    if min_val is not None and design_value < min_val:
                        violation = {
                            "code": req_code,
                            "name": req_name,
                            "type": "minimum_violation",
                            "required": f">= {min_val} {unit}",
                            "actual": f"{design_value} {unit}",
                            "severity": "error" if mandatory else "warning",
                        }

                    # TR: Maximum değer kontrolü
                    elif max_val is not None and design_value > max_val:
                        violation = {
                            "code": req_code,
                            "name": req_name,
                            "type": "maximum_violation",
                            "required": f"<= {max_val} {unit}",
                            "actual": f"{design_value} {unit}",
                            "severity": "error" if mandatory else "warning",
                        }

                    if violation:
                        if mandatory:
                            validation_results["violations"].append(violation)
                            validation_results["compliant"] = False
                        else:
                            validation_results["warnings"].append(violation)

                    validation_results["validated_requirements"].append(
                        {
                            "code": req_code,
                            "name": req_name,
                            "status": "passed" if not violation else "failed",
                            "value": design_value,
                            "unit": unit,
                        }
                    )

            return validation_results

        except Exception as e:
            logger.error(f"TR: Code validation hatası: {e}")
            return {
                "compliant": False,
                "error": str(e),
                "region": region,
                "building_type": building_type,
            }

    def _extract_design_value(
        self, design_params: Dict[str, Any], req_code: str, req_dict: Dict[str, Any]
    ) -> Optional[float]:
        """TR: Design parametrelerinden ilgili değeri çıkar"""
        try:
            # TR: Mapping table - requirement code to design parameter
            code_mappings = {
                # TR: Türkiye
                "TR_RES_001": "room_area",
                "TR_RES_002": "ceiling_height",
                "TR_RES_003": "window_ratio",
                "TR_RES_004": "ventilation_ratio",
                "TR_RES_005": "escape_distance",
                "TR_COM_001": "ceiling_height",
                "TR_COM_002": "door_width",
                "TR_COM_003": "building_coverage_ratio",
                # TR: ABD
                "IBC_RES_001": "room_area",
                "IBC_RES_002": "ceiling_height",
                "IBC_RES_003": "window_ratio",
                "IBC_COM_001": "ceiling_height",
                "IBC_COM_002": "door_width",
                # TR: Avrupa
                "EC_RES_001": "room_area",
                "EC_RES_002": "ceiling_height",
                "EC_RES_003": "energy_consumption",
                "EC_COM_001": "ceiling_height",
                "EC_COM_002": "door_width",
                # TR: Kanada
                "NBC_RES_001": "room_area",
                "NBC_RES_002": "ceiling_height",
                # TR: Singapur
                "SBC_RES_001": "room_area",
                "SBC_RES_002": "ceiling_height",
                # TR: Brezilya
                "ABNT_RES_001": "room_area",
                "ABNT_RES_002": "ceiling_height",
            }

            param_key = code_mappings.get(req_code)
            if param_key and param_key in design_params:
                return float(design_params[param_key])

            return None

        except Exception as e:
            logger.error(f"TR: Design value extraction hatası: {e}")
            return None

    def get_available_regions(self) -> List[str]:
        """TR: Mevcut bölgeleri listele"""
        return list(self._building_codes.keys())

    def get_available_building_types(self, region: str) -> List[str]:
        """TR: Belirtilen bölge için mevcut bina tiplerini listele"""
        region_codes = self._building_codes.get(region.upper(), {})
        return list(region_codes.keys())

    def search_requirements(
        self, search_term: str, region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """TR: Gereksinimlerde arama yap"""
        try:
            results = []
            regions_to_search = (
                [region.upper()] if region else self._building_codes.keys()
            )

            for region_code in regions_to_search:
                region_data = self._building_codes.get(region_code, {})

                for building_type, requirements in region_data.items():
                    for req in requirements:
                        if (
                            search_term.lower() in req.name.lower()
                            or search_term.lower() in req.description.lower()
                            or search_term.lower() in req.code.lower()
                        ):

                            results.append(
                                {
                                    "region": region_code,
                                    "building_type": building_type,
                                    "code": req.code,
                                    "name": req.name,
                                    "description": req.description,
                                    "min_value": req.min_value,
                                    "max_value": req.max_value,
                                    "unit": req.unit,
                                    "source_article": req.source_article,
                                }
                            )

            return results

        except Exception as e:
            logger.error(f"TR: Requirements search hatası: {e}")
            return []

    def get_requirement_comparison(self, requirement_name: str) -> Dict[str, Any]:
        """TR: Aynı gereksinimi farklı bölgelerde karşılaştır"""
        try:
            comparison = {"requirement_name": requirement_name, "regions": []}

            for region_code, region_data in self._building_codes.items():
                for building_type, requirements in region_data.items():
                    for req in requirements:
                        if requirement_name.lower() in req.name.lower():
                            comparison["regions"].append(
                                {
                                    "region": region_code,
                                    "building_type": building_type,
                                    "code": req.code,
                                    "min_value": req.min_value,
                                    "max_value": req.max_value,
                                    "unit": req.unit,
                                    "source": req.source_article,
                                }
                            )

            return comparison

        except Exception as e:
            logger.error(f"TR: Requirement comparison hatası: {e}")
            return {"error": str(e)}


# TR: Global instance
regional_building_codes_service = RegionalBuildingCodesService()
