from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    alert_cron_secret: str = "alert-cron-secret"
    admin_seed_email: str = "admin@biblioteca.app"
    admin_seed_password: str = "Admin123!"
    admin_seed_name: str = "Administrador"
    librarian_seed_email: str = "biblio@biblioteca.app"
    librarian_seed_password: str = "Biblio123!"
    librarian_seed_name: str = "Bibliotecario"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
