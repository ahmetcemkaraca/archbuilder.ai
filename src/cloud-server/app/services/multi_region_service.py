from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import json
from enum import Enum

try:
    import aioredis
except ImportError:
    aioredis = None  # TR: Development ortamında kullanmak için

logger = logging.getLogger(__name__)


class DataResidencyRegion(Enum):
    """TR: Data residency bölgeleri - GDPR ve diğer uyumluluk gereksinimleri için"""
    EU_WEST = "eu-west-1"  # TR: GDPR uyumlu
    US_EAST = "us-east-1"  # TR: CCPA uyumlu
    ASIA_PACIFIC = "ap-southeast-1"  # TR: Asya-Pasifik
    TURKEY = "tr-central-1"  # TR: Türkiye veri merkezleri
    CANADA = "ca-central-1"  # TR: PIPEDA uyumlu
    BRAZIL = "sa-east-1"  # TR: LGPD uyumlu


@dataclass
class RegionConfig:
    """TR: Bölge yapılandırması"""
    region_code: str
    display_name: str
    data_center_location: str
    compliance_frameworks: List[str]
    latency_target_ms: int
    redis_endpoints: List[str]
    postgres_endpoints: List[str]
    backup_region: Optional[str] = None
    currency_codes: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.currency_codes is None:
            self.currency_codes = ["USD"]
        if self.supported_languages is None:
            self.supported_languages = ["en"]


class MultiRegionService:
    """TR: Multi-region desteği ve data residency compliance servisi"""
    
    def __init__(self):
        self._region_configs: Dict[str, RegionConfig] = {}
        self._redis_pools: Dict[str, Any] = {}  # TR: aioredis.Redis type hint'i için
        self._current_region = DataResidencyRegion.TURKEY.value  # TR: Varsayılan bölge
        self._load_region_configurations()
    
    def _load_region_configurations(self) -> None:
        """TR: Bölge yapılandırmalarını yükle"""
        try:
            self._region_configs = {
                DataResidencyRegion.TURKEY.value: RegionConfig(
                    region_code="TR",
                    display_name="Türkiye",
                    data_center_location="Istanbul, Turkey",
                    compliance_frameworks=["KVKK", "GDPR"],
                    latency_target_ms=50,
                    redis_endpoints=["redis-tr-central-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-tr-central-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.EU_WEST.value,
                    currency_codes=["TRY", "USD", "EUR"],
                    supported_languages=["tr", "en"]
                ),
                
                DataResidencyRegion.EU_WEST.value: RegionConfig(
                    region_code="EU",
                    display_name="Europe West",
                    data_center_location="Dublin, Ireland",
                    compliance_frameworks=["GDPR", "DPA"],
                    latency_target_ms=30,
                    redis_endpoints=["redis-eu-west-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-eu-west-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.TURKEY.value,
                    currency_codes=["EUR", "GBP", "USD"],
                    supported_languages=["en", "de", "fr", "it", "es", "nl"]
                ),
                
                DataResidencyRegion.US_EAST.value: RegionConfig(
                    region_code="US",
                    display_name="United States East",
                    data_center_location="Virginia, USA",
                    compliance_frameworks=["CCPA", "HIPAA", "SOC2"],
                    latency_target_ms=40,
                    redis_endpoints=["redis-us-east-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-us-east-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.CANADA.value,
                    currency_codes=["USD", "CAD"],
                    supported_languages=["en", "es"]
                ),
                
                DataResidencyRegion.ASIA_PACIFIC.value: RegionConfig(
                    region_code="APAC",
                    display_name="Asia Pacific",
                    data_center_location="Singapore",
                    compliance_frameworks=["PDPA", "Privacy Act"],
                    latency_target_ms=60,
                    redis_endpoints=["redis-ap-southeast-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-ap-southeast-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.TURKEY.value,
                    currency_codes=["SGD", "AUD", "JPY", "USD"],
                    supported_languages=["en", "ja", "ko", "zh", "th"]
                ),
                
                DataResidencyRegion.CANADA.value: RegionConfig(
                    region_code="CA",
                    display_name="Canada Central",
                    data_center_location="Toronto, Canada",
                    compliance_frameworks=["PIPEDA", "Privacy Act"],
                    latency_target_ms=35,
                    redis_endpoints=["redis-ca-central-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-ca-central-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.US_EAST.value,
                    currency_codes=["CAD", "USD"],
                    supported_languages=["en", "fr"]
                ),
                
                DataResidencyRegion.BRAZIL.value: RegionConfig(
                    region_code="BR",
                    display_name="Brazil East",
                    data_center_location="Sao Paulo, Brazil",
                    compliance_frameworks=["LGPD"],
                    latency_target_ms=70,
                    redis_endpoints=["redis-sa-east-1.archbuilder.ai:6379"],
                    postgres_endpoints=["pg-sa-east-1.archbuilder.ai:5432"],
                    backup_region=DataResidencyRegion.US_EAST.value,
                    currency_codes=["BRL", "USD"],
                    supported_languages=["pt", "en", "es"]
                )
            }
            
            logger.info(f"TR: {len(self._region_configs)} bölge yapılandırması yüklendi")
            
        except Exception as e:
            logger.error(f"TR: Bölge yapılandırma yükleme hatası: {e}")
            self._region_configs = {}
    
    async def initialize_region_connections(self, region: str) -> bool:
        """TR: Belirtilen bölge için bağlantıları başlat"""
        try:
            config = self._region_configs.get(region)
            if not config:
                logger.error(f"TR: Bilinmeyen bölge: {region}")
                return False
            
            # TR: Redis bağlantı havuzu oluştur
            for redis_endpoint in config.redis_endpoints:
                if region not in self._redis_pools:
                    if aioredis:
                        redis_pool = await aioredis.from_url(
                            f"redis://{redis_endpoint}",
                            decode_responses=True,
                            retry_on_timeout=True,
                            health_check_interval=30
                        )
                        self._redis_pools[region] = redis_pool
                        logger.info(f"TR: Redis bağlantı havuzu oluşturuldu: {region}")
                    else:
                        logger.warning("TR: aioredis kütüphanesi yüklenmemiş, Redis bağlantısı oluşturulamadı")
            
            return True
            
        except Exception as e:
            logger.error(f"TR: Bölge bağlantı başlatma hatası: {e}")
            return False
    
    def get_optimal_region_for_user(self, user_location: Optional[str] = None, 
                                  compliance_requirements: Optional[List[str]] = None) -> str:
        """TR: Kullanıcı için optimal bölgeyi belirle"""
        try:
            # TR: Kullanıcı konumuna göre
            if user_location:
                location_mapping = {
                    "TR": DataResidencyRegion.TURKEY.value,
                    "EU": DataResidencyRegion.EU_WEST.value,
                    "US": DataResidencyRegion.US_EAST.value,
                    "CA": DataResidencyRegion.CANADA.value,
                    "BR": DataResidencyRegion.BRAZIL.value,
                    "APAC": DataResidencyRegion.ASIA_PACIFIC.value
                }
                
                if user_location.upper() in location_mapping:
                    return location_mapping[user_location.upper()]
            
            # TR: Compliance gereksinimlerine göre
            if compliance_requirements:
                for region_code, config in self._region_configs.items():
                    if any(req in config.compliance_frameworks for req in compliance_requirements):
                        return region_code
            
            # TR: Varsayılan bölge
            return self._current_region
            
        except Exception as e:
            logger.error(f"TR: Optimal bölge belirleme hatası: {e}")
            return self._current_region
    
    async def get_redis_client(self, region: str) -> Optional[Any]:
        """TR: Belirtilen bölge için Redis client'ı getir"""
        try:
            if region not in self._redis_pools:
                success = await self.initialize_region_connections(region)
                if not success:
                    return None
            
            return self._redis_pools.get(region)
            
        except Exception as e:
            logger.error(f"TR: Redis client getirme hatası: {e}")
            return None
    
    async def replicate_data_across_regions(self, data: Dict[str, Any], 
                                          primary_region: str,
                                          backup_regions: Optional[List[str]] = None) -> bool:
        """TR: Veriyi bölgeler arası replika et"""
        try:
            if backup_regions is None:
                primary_config = self._region_configs.get(primary_region)
                if primary_config and primary_config.backup_region:
                    backup_regions = [primary_config.backup_region]
                else:
                    backup_regions = []
            
            # TR: Ana bölgeye yaz
            primary_redis = await self.get_redis_client(primary_region)
            if primary_redis:
                await primary_redis.hset("user_data", mapping=data)
                logger.info(f"TR: Veri ana bölgeye yazıldı: {primary_region}")
            
            # TR: Backup bölgelere replika et
            for backup_region in backup_regions:
                try:
                    backup_redis = await self.get_redis_client(backup_region)
                    if backup_redis:
                        await backup_redis.hset("user_data_replica", mapping=data)
                        logger.info(f"TR: Veri backup bölgeye replike edildi: {backup_region}")
                        
                except Exception as e:
                    logger.error(f"TR: Backup bölge replikasyon hatası {backup_region}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"TR: Bölgeler arası replikasyon hatası: {e}")
            return False
    
    def get_region_compliance_info(self, region: str) -> Dict[str, Any]:
        """TR: Bölge compliance bilgisini getir"""
        config = self._region_configs.get(region)
        if not config:
            return {}
        
        return {
            "region": region,
            "display_name": config.display_name,
            "data_center_location": config.data_center_location,
            "compliance_frameworks": config.compliance_frameworks,
            "supported_currencies": config.currency_codes,
            "supported_languages": config.supported_languages,
            "latency_target_ms": config.latency_target_ms
        }
    
    def get_available_regions(self) -> List[Dict[str, Any]]:
        """TR: Mevcut bölgeleri listele"""
        regions = []
        for region_code, config in self._region_configs.items():
            regions.append({
                "code": region_code,
                "name": config.display_name,
                "location": config.data_center_location,
                "compliance": config.compliance_frameworks,
                "latency_ms": config.latency_target_ms,
                "currencies": config.currency_codes,
                "languages": config.supported_languages
            })
        
        return regions
    
    async def check_region_health(self, region: str) -> Dict[str, Any]:
        """TR: Bölge sağlık durumunu kontrol et"""
        try:
            config = self._region_configs.get(region)
            if not config:
                return {"status": "unknown", "region": region}
            
            health_status = {"region": region, "services": {}}
            
            # TR: Redis sağlık kontrolü
            try:
                redis_client = await self.get_redis_client(region)
                if redis_client:
                    await redis_client.ping()
                    health_status["services"]["redis"] = "healthy"
                else:
                    health_status["services"]["redis"] = "unavailable"
            except Exception as e:
                health_status["services"]["redis"] = f"error: {str(e)}"
            
            # TR: Genel durum
            redis_healthy = health_status["services"]["redis"] == "healthy"
            health_status["status"] = "healthy" if redis_healthy else "degraded"
            health_status["timestamp"] = datetime.utcnow().isoformat()
            
            return health_status
            
        except Exception as e:
            logger.error(f"TR: Bölge sağlık kontrolü hatası: {e}")
            return {
                "status": "error", 
                "region": region, 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_latency_metrics(self, region: str) -> Dict[str, Any]:
        """TR: Bölge latency metriklerini getir"""
        try:
            config = self._region_configs.get(region)
            if not config:
                return {}
            
            # TR: Redis latency testi
            start_time = datetime.utcnow()
            redis_client = await self.get_redis_client(region)
            
            if redis_client:
                await redis_client.ping()
                end_time = datetime.utcnow()
                latency_ms = (end_time - start_time).total_seconds() * 1000
                
                return {
                    "region": region,
                    "redis_latency_ms": round(latency_ms, 2),
                    "target_latency_ms": config.latency_target_ms,
                    "within_target": latency_ms <= config.latency_target_ms,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {"region": region, "error": "Redis unavailable"}
            
        except Exception as e:
            logger.error(f"TR: Latency metrik hatası: {e}")
            return {"region": region, "error": str(e)}
    
    def get_data_residency_compliance(self, region: str, 
                                    user_citizenship: Optional[str] = None) -> Dict[str, Any]:
        """TR: Data residency compliance durumunu kontrol et"""
        try:
            config = self._region_configs.get(region)
            if not config:
                return {"compliant": False, "reason": "Unknown region"}
            
            # TR: Temel compliance kontrolü
            compliance_info = {
                "region": region,
                "compliant": True,
                "frameworks": config.compliance_frameworks,
                "data_location": config.data_center_location,
                "recommendations": []
            }
            
            # TR: Vatandaşlık bazlı öneriler
            if user_citizenship:
                if user_citizenship == "TR" and region != DataResidencyRegion.TURKEY.value:
                    compliance_info["recommendations"].append(
                        "KVKK uyumluluğu için Türkiye bölgesi önerilir"
                    )
                elif user_citizenship in ["DE", "FR", "IT", "ES"] and "GDPR" not in config.compliance_frameworks:
                    compliance_info["recommendations"].append(
                        "GDPR uyumluluğu için AB bölgesi önerilir"
                    )
                elif user_citizenship == "US" and "CCPA" not in config.compliance_frameworks:
                    compliance_info["recommendations"].append(
                        "CCPA uyumluluğu için ABD bölgesi önerilir"
                    )
            
            return compliance_info
            
        except Exception as e:
            logger.error(f"TR: Data residency compliance kontrolü hatası: {e}")
            return {"compliant": False, "error": str(e)}
    
    async def migrate_user_data(self, user_id: str, source_region: str, 
                              target_region: str) -> bool:
        """TR: Kullanıcı verisini bölgeler arası migrate et"""
        try:
            source_redis = await self.get_redis_client(source_region)
            target_redis = await self.get_redis_client(target_region)
            
            if not source_redis or not target_redis:
                logger.error("TR: Migration için gerekli Redis bağlantıları bulunamadı")
                return False
            
            # TR: Kullanıcı verisini kaynak bölgeden oku
            user_data_key = f"user:{user_id}"
            user_data = await source_redis.hgetall(user_data_key)
            
            if not user_data:
                logger.warning(f"TR: {user_id} için veri bulunamadı")
                return True  # TR: Veri yoksa migration başarılı sayılır
            
            # TR: Hedef bölgeye yaz
            await target_redis.hset(user_data_key, mapping=user_data)
            
            # TR: Migration logunu kaydet
            migration_log = {
                "user_id": user_id,
                "source_region": source_region,
                "target_region": target_region,
                "migrated_at": datetime.utcnow().isoformat(),
                "data_size": len(str(user_data))
            }
            
            await target_redis.hset(f"migration_log:{user_id}", mapping=migration_log)
            
            logger.info(f"TR: {user_id} verisi {source_region} -> {target_region} migrate edildi")
            return True
            
        except Exception as e:
            logger.error(f"TR: Veri migration hatası: {e}")
            return False
    
    async def cleanup_region_connections(self) -> None:
        """TR: Bölge bağlantılarını temizle"""
        try:
            for region, redis_pool in self._redis_pools.items():
                if redis_pool:
                    await redis_pool.close()
                    logger.info(f"TR: {region} Redis bağlantısı kapatıldı")
            
            self._redis_pools.clear()
            
        except Exception as e:
            logger.error(f"TR: Bağlantı temizleme hatası: {e}")


# TR: Global instance
multi_region_service = MultiRegionService()