"""
Redis Cache Layer for ArchBuilder.AI

Provides high-performance caching for:
- AI model responses
- User session data
- Document processing results
- Regional configuration data
- Building code validation results
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import redis.asyncio as redis
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CacheKeyType(str, Enum):
    """Cache key types for different data categories"""

    AI_RESPONSE = "ai_response"
    USER_SESSION = "user_session"
    DOCUMENT_PROCESSING = "doc_processing"
    REGIONAL_CONFIG = "regional_config"
    BUILDING_CODE = "building_code"
    VALIDATION_RESULT = "validation_result"
    PROJECT_ANALYSIS = "project_analysis"


class CacheConfig(BaseModel):
    """Redis cache configuration"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30

    # Cache TTL settings (in seconds)
    ai_response_ttl: int = 3600  # 1 hour
    user_session_ttl: int = 1800  # 30 minutes
    document_processing_ttl: int = 7200  # 2 hours
    regional_config_ttl: int = 86400  # 24 hours
    building_code_ttl: int = 86400  # 24 hours
    validation_result_ttl: int = 1800  # 30 minutes
    project_analysis_ttl: int = 3600  # 1 hour


class CacheEntry(BaseModel):
    """Cache entry with metadata"""

    key: str
    value: Any
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    cache_type: CacheKeyType


class RedisCacheManager:
    """High-performance Redis cache manager for ArchBuilder.AI"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._redis_client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection pool"""
        try:
            self._redis_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
            )

            self._redis_client = redis.Redis(connection_pool=self._redis_pool)

            # Test connection
            await self._redis_client.ping()

            logger.info(
                "Redis cache initialized successfully",
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
            )

        except Exception as e:
            logger.error(
                "Failed to initialize Redis cache",
                error=str(e),
                host=self.config.host,
                port=self.config.port,
            )
            raise

    async def close(self) -> None:
        """Close Redis connections"""
        if self._redis_client:
            await self._redis_client.close()
        if self._redis_pool:
            await self._redis_pool.disconnect()

    def _generate_key(self, key_type: CacheKeyType, identifier: str, **kwargs) -> str:
        """Generate standardized cache key"""
        key_parts = [f"archbuilder:{key_type.value}", identifier]

        # Add additional context if provided
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")

        return ":".join(key_parts)

    def _get_ttl(self, key_type: CacheKeyType) -> int:
        """Get TTL for cache key type"""
        ttl_map = {
            CacheKeyType.AI_RESPONSE: self.config.ai_response_ttl,
            CacheKeyType.USER_SESSION: self.config.user_session_ttl,
            CacheKeyType.DOCUMENT_PROCESSING: self.config.document_processing_ttl,
            CacheKeyType.REGIONAL_CONFIG: self.config.regional_config_ttl,
            CacheKeyType.BUILDING_CODE: self.config.building_code_ttl,
            CacheKeyType.VALIDATION_RESULT: self.config.validation_result_ttl,
            CacheKeyType.PROJECT_ANALYSIS: self.config.project_analysis_ttl,
        }
        return ttl_map.get(key_type, 3600)  # Default 1 hour

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self._redis_client:
                return None

            cached_data = await self._redis_client.get(key)
            if not cached_data:
                return None

            # Deserialize cache entry
            entry_data = json.loads(cached_data)
            entry = CacheEntry(**entry_data)

            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                await self.delete(key)
                return None

            # Update access metadata
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            await self._redis_client.setex(
                key,
                self._get_ttl(entry.cache_type),
                json.dumps(entry.dict(), default=str),
            )

            logger.debug("Cache hit", key=key, access_count=entry.access_count)
            return entry.value

        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None

    async def set(
        self, key: str, value: Any, key_type: CacheKeyType, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            if not self._redis_client:
                return False

            ttl = ttl or self._get_ttl(key_type)
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            entry = CacheEntry(
                key=key, value=value, expires_at=expires_at, cache_type=key_type
            )

            await self._redis_client.setex(
                key, ttl, json.dumps(entry.dict(), default=str)
            )

            logger.debug("Cache set", key=key, ttl=ttl, cache_type=key_type.value)
            return True

        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self._redis_client:
                return False

            result = await self._redis_client.delete(key)
            logger.debug("Cache delete", key=key, deleted=bool(result))
            return bool(result)

        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            if not self._redis_client:
                return 0

            keys = await self._redis_client.keys(pattern)
            if keys:
                result = await self._redis_client.delete(*keys)
                logger.info("Cache pattern delete", pattern=pattern, deleted=result)
                return result
            return 0

        except Exception as e:
            logger.warning("Cache pattern delete failed", pattern=pattern, error=str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self._redis_client:
                return False

            result = await self._redis_client.exists(key)
            return bool(result)

        except Exception as e:
            logger.warning("Cache exists check failed", key=key, error=str(e))
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self._redis_client:
                return {}

            info = await self._redis_client.info()

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace": info.get("db0", {}).get("keys", 0),
            }

        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))
            return {}


class CacheService:
    """High-level cache service for ArchBuilder.AI operations"""

    def __init__(self, cache_manager: RedisCacheManager):
        self.cache_manager = cache_manager

    async def cache_ai_response(
        self, correlation_id: str, model: str, response: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache AI model response"""
        key = self.cache_manager._generate_key(
            CacheKeyType.AI_RESPONSE, correlation_id, model=model
        )
        return await self.cache_manager.set(
            key, response, CacheKeyType.AI_RESPONSE, ttl
        )

    async def get_ai_response(self, correlation_id: str, model: str) -> Optional[Any]:
        """Get cached AI model response"""
        key = self.cache_manager._generate_key(
            CacheKeyType.AI_RESPONSE, correlation_id, model=model
        )
        return await self.cache_manager.get(key)

    async def cache_user_session(
        self, user_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Cache user session data"""
        key = self.cache_manager._generate_key(CacheKeyType.USER_SESSION, user_id)
        return await self.cache_manager.set(
            key, session_data, CacheKeyType.USER_SESSION, ttl
        )

    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session data"""
        key = self.cache_manager._generate_key(CacheKeyType.USER_SESSION, user_id)
        return await self.cache_manager.get(key)

    async def cache_document_processing(
        self, document_id: str, processing_result: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache document processing result"""
        key = self.cache_manager._generate_key(
            CacheKeyType.DOCUMENT_PROCESSING, document_id
        )
        return await self.cache_manager.set(
            key, processing_result, CacheKeyType.DOCUMENT_PROCESSING, ttl
        )

    async def get_document_processing(self, document_id: str) -> Optional[Any]:
        """Get cached document processing result"""
        key = self.cache_manager._generate_key(
            CacheKeyType.DOCUMENT_PROCESSING, document_id
        )
        return await self.cache_manager.get(key)

    async def cache_regional_config(
        self, region: str, config_data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Cache regional configuration"""
        key = self.cache_manager._generate_key(CacheKeyType.REGIONAL_CONFIG, region)
        return await self.cache_manager.set(
            key, config_data, CacheKeyType.REGIONAL_CONFIG, ttl
        )

    async def get_regional_config(self, region: str) -> Optional[Dict[str, Any]]:
        """Get cached regional configuration"""
        key = self.cache_manager._generate_key(CacheKeyType.REGIONAL_CONFIG, region)
        return await self.cache_manager.get(key)

    async def cache_building_code_validation(
        self,
        region: str,
        building_type: str,
        validation_result: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache building code validation result"""
        key = self.cache_manager._generate_key(
            CacheKeyType.BUILDING_CODE, f"{region}:{building_type}"
        )
        return await self.cache_manager.set(
            key, validation_result, CacheKeyType.BUILDING_CODE, ttl
        )

    async def get_building_code_validation(
        self, region: str, building_type: str
    ) -> Optional[Any]:
        """Get cached building code validation result"""
        key = self.cache_manager._generate_key(
            CacheKeyType.BUILDING_CODE, f"{region}:{building_type}"
        )
        return await self.cache_manager.get(key)

    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cache entries for a user"""
        patterns = [
            f"archbuilder:{CacheKeyType.USER_SESSION.value}:{user_id}",
            f"archbuilder:{CacheKeyType.AI_RESPONSE.value}:*",
            f"archbuilder:{CacheKeyType.DOCUMENT_PROCESSING.value}:*",
        ]

        total_deleted = 0
        for pattern in patterns:
            deleted = await self.cache_manager.delete_pattern(pattern)
            total_deleted += deleted

        logger.info("User cache cleared", user_id=user_id, deleted=total_deleted)
        return total_deleted


# Global cache instance
_cache_manager: Optional[RedisCacheManager] = None
_cache_service: Optional[CacheService] = None


async def initialize_cache(config: CacheConfig) -> CacheService:
    """Initialize global cache service"""
    global _cache_manager, _cache_service

    _cache_manager = RedisCacheManager(config)
    await _cache_manager.initialize()
    _cache_service = CacheService(_cache_manager)

    return _cache_service


async def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized")
    return _cache_service


async def close_cache() -> None:
    """Close global cache connections"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.close()
