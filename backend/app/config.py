from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "HGI Radar"
    app_env: str = "development"
    log_level: str = "INFO"
    default_language: str = "fr"

    # Database
    database_url: str
    database_url_sync: str

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "mistral"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/google/callback"
    token_encryption_key: str = "change-me-32-byte-hex-key-here-00"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    # Scraping
    playwright_headless: bool = True
    scraper_proxy_url: str = ""
    linkedin_li_at_cookie: str = ""


settings = Settings()
