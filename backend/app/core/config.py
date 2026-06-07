from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_CHAVE_PADRAO = "mude-esta-chave-em-producao-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    APP_NAME: str = "Projetista V2 API"
    APP_ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://projetista:projetista@localhost:5432/projetista_v2"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # JWT
    SECRET_KEY: str = _CHAVE_PADRAO
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480      # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # URL base do frontend (usada nos links de email)
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        # Render fornece "postgres://" — normalizar para o driver psycopg3
        if value.startswith("postgres://"):
            url = value.replace("postgres://", "postgresql+psycopg://", 1)
            # Render exige SSL — adicionar sslmode=require se não presente
            if "sslmode" not in url:
                sep = "&" if "?" in url else "?"
                url += f"{sep}sslmode=require"
            return url
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def validar_producao(self) -> "Settings":
        if self.APP_ENV == "production":
            if self.SECRET_KEY == _CHAVE_PADRAO:
                raise ValueError(
                    "SECRET_KEY ainda é o valor padrão. "
                    "Gere uma chave segura com: openssl rand -hex 32"
                )
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "CORS_ORIGINS não pode ser ['*'] em produção. "
                    "Defina as origens permitidas no .env"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
