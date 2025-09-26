"""
HashiCorp Vault Integration for ArchBuilder.AI
Provides secure secret management, rotation, and environment-based configuration injection.
"""
from __future__ import annotations

import os
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import hvac
from hvac import Client as VaultClient
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from app.core.logging import get_logger

logger = get_logger(__name__)


class VaultConfig(BaseSettings):
    """Vault configuration from environment variables"""
    
    vault_url: str = Field(default="http://localhost:8200", env="VAULT_URL")
    vault_token: Optional[str] = Field(default=None, env="VAULT_TOKEN")
    vault_role_id: Optional[str] = Field(default=None, env="VAULT_ROLE_ID")
    vault_secret_id: Optional[str] = Field(default=None, env="VAULT_SECRET_ID")
    vault_mount_path: str = Field(default="secret", env="VAULT_MOUNT_PATH")
    vault_namespace: Optional[str] = Field(default=None, env="VAULT_NAMESPACE")
    vault_ca_cert: Optional[str] = Field(default=None, env="VAULT_CACERT")
    vault_client_cert: Optional[str] = Field(default=None, env="VAULT_CLIENT_CERT")
    vault_client_key: Optional[str] = Field(default=None, env="VAULT_CLIENT_KEY")
    
    # Development/fallback settings
    use_vault: bool = Field(default=True, env="USE_VAULT")
    vault_dev_mode: bool = Field(default=False, env="VAULT_DEV_MODE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class SecretMetadata(BaseModel):
    """Metadata for a secret"""
    
    path: str
    version: int
    created_time: datetime
    deletion_time: Optional[datetime] = None
    destroyed: bool = False
    custom_metadata: Dict[str, str] = Field(default_factory=dict)


class SecretValue(BaseModel):
    """A secret with its metadata"""
    
    data: Dict[str, Any]
    metadata: SecretMetadata
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from secret data"""
        return self.data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in secret data"""
        return key in self.data


class VaultSecretManager:
    """
    HashiCorp Vault client for secure secret management.
    Supports multiple authentication methods and automatic token renewal.
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig()
        self.client: Optional[VaultClient] = None
        self.authenticated = False
        self.token_expires_at: Optional[datetime] = None
        self._secret_cache: Dict[str, SecretValue] = {}
        
        # Initialize client if Vault is enabled
        if self.config.use_vault:
            asyncio.create_task(self._initialize_client())
    
    async def _initialize_client(self) -> None:
        """Initialize Vault client and authenticate"""
        try:
            # Create Vault client
            self.client = hvac.Client(
                url=self.config.vault_url,
                namespace=self.config.vault_namespace,
                verify=self._get_tls_config()
            )
            
            # Authenticate
            await self._authenticate()
            
            logger.info("Vault client initialized successfully")
            
        except Exception as e:
            if not self.config.vault_dev_mode:
                logger.error(f"Failed to initialize Vault client: {e}")
                raise
            else:
                logger.warning(f"Vault initialization failed, continuing in dev mode: {e}")
    
    def _get_tls_config(self) -> Union[bool, str]:
        """Get TLS configuration for Vault client"""
        if self.config.vault_ca_cert:
            return self.config.vault_ca_cert
        
        # In production, always verify TLS
        if not self.config.vault_dev_mode:
            return True
        
        # In dev mode, might skip verification
        return not self.config.vault_url.startswith("http://")
    
    async def _authenticate(self) -> None:
        """Authenticate with Vault using configured method"""
        
        if not self.client:
            raise ValueError("Vault client not initialized")
        
        try:
            # Method 1: Direct token authentication
            if self.config.vault_token:
                self.client.token = self.config.vault_token
                
                # Verify token is valid
                if self.client.is_authenticated():
                    self.authenticated = True
                    await self._set_token_expiry()
                    logger.info("Authenticated with Vault using direct token")
                    return
            
            # Method 2: AppRole authentication
            if self.config.vault_role_id and self.config.vault_secret_id:
                auth_response = self.client.auth.approle.login(
                    role_id=self.config.vault_role_id,
                    secret_id=self.config.vault_secret_id
                )
                
                if auth_response and 'auth' in auth_response:
                    self.client.token = auth_response['auth']['client_token']
                    self.authenticated = True
                    await self._set_token_expiry()
                    logger.info("Authenticated with Vault using AppRole")
                    return
            
            # Method 3: Kubernetes authentication (if running in K8s)
            jwt_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
            if os.path.exists(jwt_path):
                with open(jwt_path) as f:
                    jwt_token = f.read().strip()
                
                auth_response = self.client.auth.kubernetes.login(
                    role="archbuilder-role",  # Configure this role in Vault
                    jwt=jwt_token
                )
                
                if auth_response and 'auth' in auth_response:
                    self.client.token = auth_response['auth']['client_token']
                    self.authenticated = True
                    await self._set_token_expiry()
                    logger.info("Authenticated with Vault using Kubernetes auth")
                    return
            
            raise ValueError("No valid authentication method available")
            
        except Exception as e:
            logger.error(f"Vault authentication failed: {e}")
            if not self.config.vault_dev_mode:
                raise
            else:
                logger.warning("Continuing without Vault authentication in dev mode")
    
    async def _set_token_expiry(self) -> None:
        """Set token expiry time from Vault response"""
        try:
            if self.client and self.client.token:
                token_info = self.client.lookup_token()
                if token_info and 'data' in token_info:
                    ttl = token_info['data'].get('ttl', 0)
                    if ttl > 0:
                        self.token_expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                        
                        # Schedule token renewal at 80% of TTL
                        renewal_time = ttl * 0.8
                        asyncio.create_task(self._schedule_token_renewal(renewal_time))
                        
        except Exception as e:
            logger.warning(f"Failed to get token TTL: {e}")
    
    async def _schedule_token_renewal(self, delay_seconds: float) -> None:
        """Schedule automatic token renewal"""
        try:
            await asyncio.sleep(delay_seconds)
            await self._renew_token()
        except Exception as e:
            logger.error(f"Token renewal failed: {e}")
            # Try to re-authenticate
            await self._authenticate()
    
    async def _renew_token(self) -> None:
        """Renew the current Vault token"""
        try:
            if self.client and self.authenticated:
                renewal_response = self.client.renew_token()
                if renewal_response:
                    await self._set_token_expiry()
                    logger.info("Vault token renewed successfully")
                
        except Exception as e:
            logger.error(f"Token renewal failed: {e}")
            # Re-authenticate on renewal failure
            await self._authenticate()
    
    async def get_secret(self, path: str, version: Optional[int] = None, use_cache: bool = True) -> Optional[SecretValue]:
        """
        Retrieve a secret from Vault.
        
        Args:
            path: Secret path (e.g., "app/database", "app/api-keys")
            version: Specific version to retrieve (default: latest)
            use_cache: Whether to use cached value if available
            
        Returns:
            SecretValue object or None if not found
        """
        
        # Return cached value if available and cache is enabled
        cache_key = f"{path}:{version or 'latest'}"
        if use_cache and cache_key in self._secret_cache:
            return self._secret_cache[cache_key]
        
        # If Vault is disabled or not available, try environment fallback
        if not self.config.use_vault or not self.authenticated:
            return await self._get_secret_from_env(path)
        
        try:
            if not self.client:
                raise ValueError("Vault client not initialized")
            
            # Construct full path
            full_path = f"{self.config.vault_mount_path}/data/{path}"
            
            # Get secret with optional version
            params = {"version": version} if version else {}
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.config.vault_mount_path,
                **params
            )
            
            if response and 'data' in response:
                secret_data = response['data']['data']
                metadata_raw = response['data']['metadata']
                
                # Parse metadata
                metadata = SecretMetadata(
                    path=path,
                    version=metadata_raw['version'],
                    created_time=datetime.fromisoformat(metadata_raw['created_time'].replace('Z', '+00:00')),
                    deletion_time=datetime.fromisoformat(metadata_raw['deletion_time'].replace('Z', '+00:00')) if metadata_raw.get('deletion_time') else None,
                    destroyed=metadata_raw.get('destroyed', False),
                    custom_metadata=metadata_raw.get('custom_metadata', {})
                )
                
                secret_value = SecretValue(data=secret_data, metadata=metadata)
                
                # Cache the result
                self._secret_cache[cache_key] = secret_value
                
                logger.debug(f"Retrieved secret from Vault: {path}")
                return secret_value
            
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Secret not found in Vault: {path}")
            return await self._get_secret_from_env(path)
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {path} - {e}")
            return await self._get_secret_from_env(path)
        
        return None
    
    async def _get_secret_from_env(self, path: str) -> Optional[SecretValue]:
        """Fallback to environment variables when Vault is unavailable"""
        
        logger.debug(f"Trying environment fallback for secret: {path}")
        
        # Convert path to environment variable format
        # e.g., "app/database" -> "APP_DATABASE_*"
        env_prefix = path.replace('/', '_').replace('-', '_').upper()
        
        # Common secret keys to look for
        secret_keys = ['URL', 'HOST', 'PORT', 'USER', 'USERNAME', 'PASSWORD', 'KEY', 'SECRET', 'TOKEN']
        
        secret_data = {}
        for key in secret_keys:
            env_var = f"{env_prefix}_{key}"
            value = os.environ.get(env_var)
            if value:
                secret_data[key.lower()] = value
        
        # Also try direct path as env var
        direct_env = os.environ.get(env_prefix)
        if direct_env:
            secret_data['value'] = direct_env
        
        if secret_data:
            metadata = SecretMetadata(
                path=path,
                version=1,
                created_time=datetime.utcnow(),
                custom_metadata={"source": "environment"}
            )
            
            return SecretValue(data=secret_data, metadata=metadata)
        
        return None
    
    async def put_secret(self, path: str, secret_data: Dict[str, Any], custom_metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Store a secret in Vault.
        
        Args:
            path: Secret path
            secret_data: Secret data to store
            custom_metadata: Optional custom metadata
            
        Returns:
            True if successful, False otherwise
        """
        
        if not self.config.use_vault or not self.authenticated or not self.client:
            logger.warning("Cannot store secret: Vault not available")
            return False
        
        try:
            # Store secret with metadata
            options = {}
            if custom_metadata:
                options['metadata'] = custom_metadata
            
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                mount_point=self.config.vault_mount_path,
                **options
            )
            
            if response:
                logger.info(f"Secret stored successfully: {path}")
                
                # Clear cache for this path
                cache_keys_to_remove = [key for key in self._secret_cache.keys() if key.startswith(f"{path}:")]
                for key in cache_keys_to_remove:
                    del self._secret_cache[key]
                
                return True
            
        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {path} - {e}")
        
        return False
    
    async def delete_secret(self, path: str, versions: Optional[List[int]] = None) -> bool:
        """
        Delete secret versions from Vault.
        
        Args:
            path: Secret path
            versions: List of versions to delete (default: all versions)
            
        Returns:
            True if successful, False otherwise
        """
        
        if not self.config.use_vault or not self.authenticated or not self.client:
            logger.warning("Cannot delete secret: Vault not available")
            return False
        
        try:
            if versions:
                # Delete specific versions
                self.client.secrets.kv.v2.delete_secret_versions(
                    path=path,
                    versions=versions,
                    mount_point=self.config.vault_mount_path
                )
            else:
                # Delete all versions (soft delete)
                self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path,
                    mount_point=self.config.vault_mount_path
                )
            
            logger.info(f"Secret deleted: {path}")
            
            # Clear cache
            cache_keys_to_remove = [key for key in self._secret_cache.keys() if key.startswith(f"{path}:")]
            for key in cache_keys_to_remove:
                del self._secret_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {path} - {e}")
            return False
    
    async def rotate_secret(self, path: str, new_secret_data: Dict[str, Any]) -> bool:
        """
        Rotate a secret by creating a new version.
        
        Args:
            path: Secret path
            new_secret_data: New secret data
            
        Returns:
            True if successful, False otherwise
        """
        return await self.put_secret(path, new_secret_data, {"rotated_at": datetime.utcnow().isoformat()})
    
    async def list_secrets(self, path: str = "") -> List[str]:
        """
        List all secrets under a given path.
        
        Args:
            path: Path to list (default: root)
            
        Returns:
            List of secret paths
        """
        
        if not self.config.use_vault or not self.authenticated or not self.client:
            return []
        
        try:
            list_path = f"{self.config.vault_mount_path}/metadata"
            if path:
                list_path = f"{list_path}/{path}"
            
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self.config.vault_mount_path
            )
            
            if response and 'data' in response and 'keys' in response['data']:
                return response['data']['keys']
                
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
        
        return []
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Synchronous method to get configuration values.
        First tries Vault, then falls back to environment variables.
        """
        try:
            # Try to get from cache first
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't wait for async calls
                # Fall back to environment
                return os.environ.get(key, default)
            
            # Try async get_secret
            secret = loop.run_until_complete(self.get_secret(f"config/{key}"))
            if secret and 'value' in secret.data:
                return secret.data['value']
                
        except Exception:
            pass
        
        # Fallback to environment
        return os.environ.get(key, default)


# Global secret manager instance
_secret_manager: Optional[VaultSecretManager] = None


def get_secret_manager() -> VaultSecretManager:
    """Get or create global secret manager instance"""
    global _secret_manager
    
    if _secret_manager is None:
        _secret_manager = VaultSecretManager()
    
    return _secret_manager


async def get_secret(path: str, key: Optional[str] = None, default: Any = None) -> Any:
    """
    Convenience function to get a secret value.
    
    Args:
        path: Secret path in Vault
        key: Specific key within the secret (optional)
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    manager = get_secret_manager()
    secret = await manager.get_secret(path)
    
    if secret:
        if key:
            return secret.get(key, default)
        else:
            return secret.data
    
    return default


# Configuration class that automatically loads from Vault/environment
class SecureSettings(BaseSettings):
    """
    Base settings class that automatically loads sensitive values from Vault.
    Extends pydantic-settings to support Vault integration.
    """
    
    def __init__(self, **kwargs):
        # Initialize secret manager
        self._secret_manager = get_secret_manager()
        super().__init__(**kwargs)
    
    @classmethod
    def from_vault(cls, vault_path: str = "app/config"):
        """Create settings instance loading from Vault path"""
        
        instance = cls()
        
        # Try to load from Vault
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            secret = loop.run_until_complete(
                instance._secret_manager.get_secret(vault_path)
            )
            
            if secret:
                # Update instance with Vault data
                for key, value in secret.data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
            
        except Exception as e:
            logger.warning(f"Failed to load settings from Vault: {e}")
        
        return instance


# Example usage for ArchBuilder.AI configuration
class ArchBuilderSecureConfig(SecureSettings):
    """ArchBuilder.AI secure configuration with Vault integration"""
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    database_password: str = Field(env="DATABASE_PASSWORD")
    
    # AI Services
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    azure_openai_key: str = Field(env="AZURE_OPENAI_KEY")
    azure_openai_endpoint: str = Field(env="AZURE_OPENAI_ENDPOINT")
    vertex_ai_project_id: str = Field(env="VERTEX_AI_PROJECT_ID")
    vertex_ai_location: str = Field(default="us-central1", env="VERTEX_AI_LOCATION")
    
    # Authentication
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    # Encryption
    encryption_key: str = Field(env="ENCRYPTION_KEY")
    
    # External Services
    stripe_secret_key: str = Field(env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(env="STRIPE_WEBHOOK_SECRET")
    
    # Email/SMS
    sendgrid_api_key: str = Field(env="SENDGRID_API_KEY")
    twilio_auth_token: str = Field(env="TWILIO_AUTH_TOKEN")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Utility functions for secret rotation
async def setup_secret_rotation():
    """Setup automatic secret rotation for sensitive keys"""
    
    manager = get_secret_manager()
    
    # Define rotation schedules
    rotation_schedule = {
        "app/jwt-keys": timedelta(days=90),     # JWT keys every 90 days
        "app/encryption": timedelta(days=365),   # Encryption keys yearly
        "app/api-keys": timedelta(days=180),    # API keys every 6 months
    }
    
    for path, interval in rotation_schedule.items():
        asyncio.create_task(_schedule_rotation(manager, path, interval))


async def _schedule_rotation(manager: VaultSecretManager, path: str, interval: timedelta):
    """Schedule periodic secret rotation"""
    while True:
        try:
            await asyncio.sleep(interval.total_seconds())
            
            # Check if secret needs rotation
            secret = await manager.get_secret(path)
            if secret and secret.metadata.custom_metadata.get('auto_rotate') == 'true':
                logger.info(f"Rotating secret: {path}")
                
                # Generate new secret (implementation depends on secret type)
                new_secret_data = await _generate_new_secret(path, secret.data)
                
                # Rotate the secret
                success = await manager.rotate_secret(path, new_secret_data)
                if success:
                    logger.info(f"Secret rotation completed: {path}")
                else:
                    logger.error(f"Secret rotation failed: {path}")
                    
        except Exception as e:
            logger.error(f"Secret rotation error for {path}: {e}")


async def _generate_new_secret(path: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate new secret data based on secret type"""
    
    import secrets
    import string
    
    if "jwt" in path.lower():
        # Generate new JWT secret
        return {
            "key": secrets.token_urlsafe(64),
            "algorithm": current_data.get("algorithm", "HS256")
        }
    
    elif "encryption" in path.lower():
        # Generate new encryption key
        return {
            "key": secrets.token_bytes(32).hex(),
            "algorithm": current_data.get("algorithm", "AES-256-GCM")
        }
    
    elif "api" in path.lower():
        # Generate new API key
        alphabet = string.ascii_letters + string.digits
        return {
            "key": ''.join(secrets.choice(alphabet) for _ in range(32)),
            "created_at": datetime.utcnow().isoformat()
        }
    
    else:
        # Default: generate random string
        return {
            "value": secrets.token_urlsafe(32),
            "rotated_at": datetime.utcnow().isoformat()
        }