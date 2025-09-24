from __future__ import annotations

from pydantic import BaseSettings, Field, HttpUrl


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Notlar (TR): Varsayılanlar geliştirme içindir. Production'da env üzerinden
    geçersiz kılınmalıdır. Secrets asla koda yazılmaz.
    """

    # Core
    app_name: str = Field(default="ArchBuilder Cloud Server")
    log_level: str = Field(default="INFO")

    # RAGFlow integration
    ragflow_base_url: HttpUrl | str = Field(default="http://localhost")
    ragflow_api_key: str | None = Field(default=None)
    ragflow_api_version: str = Field(default="v1")
    ragflow_timeout_seconds: int = Field(default=30)

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


settings = Settings()


