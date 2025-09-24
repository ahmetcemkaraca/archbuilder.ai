from __future__ import annotations

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Notlar (TR): Varsayılanlar geliştirme içindir. Production'da env üzerinden
    geçersiz kılınmalıdır. Secrets asla koda yazılmaz.
    """

    # Core
    app_name: str = Field(default="ArchBuilder Cloud Server")
    log_level: str = Field(default="INFO")
    auth_dev_mode: bool = Field(default=False)
    jwt_secret: str | None = Field(default=None)

    # RAGFlow integration
    ragflow_base_url: HttpUrl | str = Field(default="http://localhost")
    ragflow_api_key: str | None = Field(default=None)
    ragflow_api_version: str = Field(default="v1")
    ragflow_timeout_seconds: int = Field(default=30)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()


