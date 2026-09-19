"""Application configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "sqlite:///./assiette.db"
    groq_api_key: str = ""
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"
    secret_key: str = _DEFAULT_SECRET
    allowed_student_domains: str = "essec.edu,centralesupelec.fr,u-paris.fr,sorbonne-universite.fr"
    cors_origins: str = ""
    rate_limit_per_minute: int = 30
    trusted_proxy_count: int = 1
    freshness_warn_days: int = 14
    freshness_refuse_days: int = 30
    sentry_dsn: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "assiette@localhost"
    resend_api_key: str = ""
    auth_token_ttl_minutes: int = 30
    session_ttl_days: int = 7
    serve_frontend: bool = True
    auto_init_db: bool = False
    refresh_token: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""
    redis_url: str = ""
    csp_policy: str = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )

    @property
    def student_domains(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_student_domains.split(",") if d.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        if self.env.lower() == "production":
            return True
        import os

        return os.environ.get("VERCEL_ENV", "").lower() == "production"

    @model_validator(mode="after")
    def _reject_default_secret_in_production(self) -> Settings:
        import os

        hosted_prod = os.environ.get("VERCEL_ENV", "").lower() == "production"
        if self.env.lower() == "production" or hosted_prod:
            if self.secret_key == _DEFAULT_SECRET or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be a unique value of at least 32 characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
