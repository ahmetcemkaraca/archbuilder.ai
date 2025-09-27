from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.services.multi_region_service import multi_region_service
from app.services.currency_service import currency_service
from app.services.regional_building_codes_service import regional_building_codes_service
from app.services.regional_config_service import RegionalConfigService
from app.core.exceptions import envelope

router = APIRouter(prefix="/api/v1/regional", tags=["regional"])

# TR: Pydantic models
class RegionInfo(BaseModel):
    region: str = Field(..., description="Bölge kodu")
    user_citizenship: Optional[str] = Field(None, description="Kullanıcı vatandaşlığı")


class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., description="Çevrilecek miktar")
    from_currency: str = Field(..., description="Kaynak para birimi")
    to_currency: str = Field(..., description="Hedef para birimi")
    region: Optional[str] = Field(None, description="Bölge")


class DesignValidationRequest(BaseModel):
    design_params: Dict[str, Any] = Field(..., description="Tasarım parametreleri")
    region: str = Field(..., description="Bölge kodu")
    building_type: str = Field(..., description="Bina tipi")


class SubscriptionPricingRequest(BaseModel):
    base_usd_price: float = Field(..., description="USD cinsinden temel fiyat")
    target_currency: str = Field(..., description="Hedef para birimi")
    region: Optional[str] = Field(None, description="Bölge")


# TR: Regional service instance
regional_config = RegionalConfigService()


@router.get("/regions", summary="Mevcut bölgeleri listele")
async def get_available_regions():
    """TR: Mevcut bölgeleri ve detaylarını listele"""
    try:
        regions = multi_region_service.get_available_regions()
        return envelope(True, regions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{region}/compliance", summary="Bölge compliance bilgisi")
async def get_region_compliance(region: str, user_citizenship: Optional[str] = Query(None)):
    """TR: Belirtilen bölge için compliance bilgisini getir"""
    try:
        compliance_info = multi_region_service.get_data_residency_compliance(region, user_citizenship)
        return envelope(True, compliance_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{region}/health", summary="Bölge sağlık durumu")
async def get_region_health(region: str):
    """TR: Belirtilen bölgenin sağlık durumunu kontrol et"""
    try:
        health_status = await multi_region_service.check_region_health(region)
        return envelope(True, health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{region}/latency", summary="Bölge latency metrikleri")
async def get_region_latency(region: str):
    """TR: Belirtilen bölgenin latency metriklerini getir"""
    try:
        latency_metrics = await multi_region_service.get_latency_metrics(region)
        return envelope(True, latency_metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regions/optimal", summary="Optimal bölge önerisi")
async def get_optimal_region(region_info: RegionInfo):
    """TR: Kullanıcı için optimal bölgeyi belirle"""
    try:
        compliance_requirements = []
        if region_info.user_citizenship:
            # TR: Vatandaşlığa göre compliance gereksinimleri
            citizenship_compliance = {
                "TR": ["KVKK", "GDPR"],
                "DE": ["GDPR"],
                "FR": ["GDPR"],
                "US": ["CCPA"],
                "CA": ["PIPEDA"],
                "BR": ["LGPD"]
            }
            compliance_requirements = citizenship_compliance.get(region_info.user_citizenship, [])
        
        optimal_region = multi_region_service.get_optimal_region_for_user(
            region_info.region, 
            compliance_requirements
        )
        
        region_details = multi_region_service.get_region_compliance_info(optimal_region)
        
        return envelope(True, {
            "optimal_region": optimal_region,
            "details": region_details,
            "compliance_requirements": compliance_requirements
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies", summary="Desteklenen para birimlerini listele")
async def get_supported_currencies(region: Optional[str] = Query(None)):
    """TR: Desteklenen para birimlerini listele"""
    try:
        currencies = currency_service.get_supported_currencies(region)
        return envelope(True, currencies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies/{currency_code}", summary="Para birimi detayları")
async def get_currency_info(currency_code: str):
    """TR: Belirtilen para biriminin detaylarını getir"""
    try:
        currency_info = currency_service.get_currency_info(currency_code)
        return envelope(True, currency_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/currencies/convert", summary="Para birimi çevirisi")
async def convert_currency(conversion_request: CurrencyConversionRequest):
    """TR: Para birimi çevirisi yap"""
    try:
        converted_amount = currency_service.convert_currency(
            conversion_request.amount,
            conversion_request.from_currency,
            conversion_request.to_currency
        )
        
        if converted_amount is None:
            raise HTTPException(
                status_code=400, 
                detail=f"Conversion not available: {conversion_request.from_currency} -> {conversion_request.to_currency}"
            )
        
        formatted_price = currency_service.format_currency(
            converted_amount, 
            conversion_request.to_currency,
            conversion_request.region
        )
        
        return envelope(True, {
            "original_amount": conversion_request.amount,
            "original_currency": conversion_request.from_currency,
            "converted_amount": float(converted_amount),
            "target_currency": conversion_request.to_currency,
            "formatted_price": formatted_price
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/currencies/validate", summary="Para birimi bölge uygunluğu")
async def validate_currency_for_region(currency_code: str, region: str):
    """TR: Para biriminin bölge için uygunluğunu kontrol et"""
    try:
        validation_result = currency_service.validate_currency_for_region(currency_code, region)
        return envelope(True, validation_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/subscription", summary="Subscription fiyat hesaplama")
async def calculate_subscription_pricing(pricing_request: SubscriptionPricingRequest):
    """TR: Subscription fiyatını hedef para birimine çevir"""
    try:
        pricing_info = currency_service.calculate_subscription_price(
            pricing_request.base_usd_price,
            pricing_request.target_currency,
            pricing_request.region
        )
        return envelope(True, pricing_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/building-codes/regions", summary="Yapı yönetmeliği bölgeleri")
async def get_building_code_regions():
    """TR: Yapı yönetmeliği desteklenen bölgeleri listele"""
    try:
        regions = regional_building_codes_service.get_available_regions()
        return envelope(True, regions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/building-codes/{region}/types", summary="Bina tipleri")
async def get_building_types(region: str):
    """TR: Belirtilen bölge için desteklenen bina tiplerini listele"""
    try:
        building_types = regional_building_codes_service.get_available_building_types(region)
        return envelope(True, building_types)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/building-codes/{region}/{building_type}/requirements", summary="Yapı gereksinimleri")
async def get_building_requirements(region: str, building_type: str):
    """TR: Belirtilen bölge ve bina tipi için yapı gereksinimlerini getir"""
    try:
        requirements = regional_building_codes_service.get_building_requirements(region, building_type)
        return envelope(True, requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/building-codes/validate", summary="Tasarım yapı yönetmeliği doğrulaması")
async def validate_design_against_codes(validation_request: DesignValidationRequest):
    """TR: Tasarımı yapı yönetmeliklerine göre doğrula"""
    try:
        validation_result = regional_building_codes_service.validate_design_against_codes(
            validation_request.design_params,
            validation_request.region,
            validation_request.building_type
        )
        return envelope(True, validation_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/building-codes/search", summary="Yapı gereksinimi arama")
async def search_building_requirements(
    search_term: str = Query(..., description="Arama terimi"),
    region: Optional[str] = Query(None, description="Bölge filtresi")
):
    """TR: Yapı gereksinimlerinde arama yap"""
    try:
        search_results = regional_building_codes_service.search_requirements(search_term, region)
        return envelope(True, search_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/building-codes/compare/{requirement_name}", summary="Gereksinim karşılaştırması")
async def compare_requirement_across_regions(requirement_name: str):
    """TR: Aynı gereksinimi farklı bölgelerde karşılaştır"""
    try:
        comparison = regional_building_codes_service.get_requirement_comparison(requirement_name)
        return envelope(True, comparison)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/i18n/languages", summary="Desteklenen diller")
async def get_supported_languages():
    """TR: Desteklenen dilleri listele"""
    try:
        languages = regional_config.get_available_languages()
        return envelope(True, languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/i18n/translate/{language}/{key}", summary="Çeviri getir")
async def get_translation(language: str, key: str):
    """TR: Belirtilen dil ve key için çeviri getir"""
    try:
        translation = regional_config.get_translation(key, language)
        return envelope(True, {"key": key, "language": language, "translation": translation})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{region}", summary="Bölgesel yapılandırma")
async def get_regional_config(region: str):
    """TR: Belirtilen bölgenin yapılandırmasını getir"""
    try:
        config = regional_config.get_regional_config(region)
        return envelope(True, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/format/number", summary="Sayı formatları")
async def format_number(
    value: float = Query(..., description="Formatlanacak sayı"),
    region: str = Query(..., description="Bölge kodu")
):
    """TR: Sayıyı bölgesel formata göre formatla"""
    try:
        formatted_number = regional_config.format_number(value, region)
        return envelope(True, {
            "original_value": value,
            "region": region,
            "formatted_number": formatted_number
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rates/info", summary="Döviz kuru bilgileri")
async def get_exchange_rate_info():
    """TR: Döviz kuru bilgilerini getir"""
    try:
        rate_info = currency_service.get_exchange_rate_info()
        return envelope(True, rate_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))