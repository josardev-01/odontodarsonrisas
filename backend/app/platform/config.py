from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DAR_SONRISAS_", env_file=".env", extra="ignore"
    )

    app_name: str = "Dar Sonrisas API"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./dar_sonrisas_dev.db"
    clinic_timezone: str = "America/Asuncion"
    cors_origins: list[str] = Field(default_factory=list)
    sql_echo: bool = False
    auto_create_schema: bool = Field(
        default=False,
        description="Convenience only; production must use Alembic migrations.",
    )
    seed_synthetic_professionals: bool = True
    bootstrap_token: SecretStr | None = Field(default=None, description="One-use initial admin bootstrap secret.")
    session_ttl_hours: int = Field(default=8, ge=1, le=168)
    session_cookie_secure: bool = False

    def validate_runtime(self) -> None:
        if self.environment.lower() == "production" and self.auto_create_schema:
            raise RuntimeError("Auto schema creation is forbidden in production")
        if self.environment.lower() == "production" and self.seed_synthetic_professionals:
            raise RuntimeError("Synthetic seeds are forbidden in production")
        if self.environment.lower() == "production" and "*" in self.cors_origins:
            raise RuntimeError("Wildcard CORS is forbidden in production")
        if self.environment.lower() == "production" and not self.session_cookie_secure:
            raise RuntimeError("Secure session cookies are mandatory in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
