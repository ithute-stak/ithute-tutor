from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings owned entirely by Tutor.

    Tutor does not depend on any other Ithute product for identity, sessions,
    notifications, database access, or deployment configuration.
    """

    # Tutor-owned PostgreSQL database.
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "tutor-db"
    DB_PORT: int = 5432
    DB_USER: str = "ithute_tutor"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ithute_tutor"

    # Public Tutor URLs.
    TUTOR_PUBLIC_URL: str = "https://tutor.ithute.co.ls"
    TUTOR_FRONTEND_URL: str = "https://tutor.ithute.co.ls"

    # Tutor-owned authentication and session settings.
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ACCESS_COOKIE_NAME: str = "ithute_tutor_access"
    REFRESH_COOKIE_NAME: str = "ithute_tutor_refresh"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    RATE_LIMIT: str = "100/minute"

    # Optional M-Pesa integration. Empty values keep the core Tutor API bootable.
    MPESA_API_KEY: str = ""
    MPESA_PUBLIC_KEY: str = ""
    MPESA_BASE_URL: str = ""
    MPESA_MARKET: str = ""
    MPESA_COUNTRY: str = "LS"
    MPESA_CURRENCY: str = "LSL"
    MPESA_SHORTCODE: str = ""
    MPESA_MODEL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        return (
            f"postgresql+psycopg2://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )

    @property
    def refresh_cookie_max_age_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    def require_secret_key(self) -> str:
        secret = self.SECRET_KEY.strip()
        if len(secret) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters")
        return secret


settings = Settings()
