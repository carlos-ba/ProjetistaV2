from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Projetista V2 API"
    APP_ENV: str = "production"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://projetista:projetista@localhost:5432/projetista_v2"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # JWT
    SECRET_KEY: str = "mude-esta-chave-em-producao-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480      # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
