import json
from typing import Annotated, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LiftAndPlate API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # CORS Origins. The env var may be a JSON list or comma-separated; a typo here must not stop the API starting.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Also allowed in production: every Vercel address of the gym-ai frontend project (production, git branch and
    # per-deployment URLs; Vercel shortens deployment URLs to e.g. gym-gosglpd59-<team>.vercel.app), so a new
    # deployment never needs CORS_ORIGINS updated.
    CORS_ORIGIN_REGEX: str = (
        r"^https://(gym-ai(-[a-z0-9-]+)?|gym-[a-z0-9-]*-ghostsami96-9088s-projects)\.vercel\.app$"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            text = value.strip()
            try:
                value = json.loads(text.replace("'", '"')) if text.startswith("[") else text.split(",")
            except json.JSONDecodeError:
                value = text.strip("[]").split(",")
        return [str(origin).strip().strip("'\"").rstrip("/") for origin in value if str(origin).strip()]

    # JWT Security Configurations
    JWT_SECRET_KEY: str = "gym_ai_super_secret_jwt_key_change_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7    # 7 days

    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "gym_ai_user"
    POSTGRES_PASSWORD: str = "gym_ai_password"
    POSTGRES_DB: str = "gym_ai_db"
    DATABASE_URL: Union[str, None] = None

    # Meal Snap photo recognition (Google Gemini API). Without a key the Food page still works with manual entry.
    GEMINI_API_KEY: Union[str, None] = None
    GEMINI_MODEL: str = "gemini-flash-lite-latest"

    # WhatsApp Coach (Meta WhatsApp Cloud API). Without WHATSAPP_TOKEN replies are logged instead of sent, and
    # without WHATSAPP_APP_SECRET the webhook rejects every message.
    WHATSAPP_TOKEN: Union[str, None] = None
    WHATSAPP_PHONE_NUMBER_ID: Union[str, None] = None
    WHATSAPP_APP_SECRET: Union[str, None] = None
    WHATSAPP_VERIFY_TOKEN: Union[str, None] = None
    WHATSAPP_BOT_NUMBER: Union[str, None] = None  # digits only, with country code, e.g. 923001234567
    WHATSAPP_API_VERSION: str = "v23.0"
    # Unofficial gateway (whatsapp-gateway/, linked as a WhatsApp Web device). Shared secret for its signed calls.
    WHATSAPP_GATEWAY_SECRET: Union[str, None] = None

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
