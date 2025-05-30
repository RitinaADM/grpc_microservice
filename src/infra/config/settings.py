from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class DatabaseType(Enum):
    """Типы поддерживаемых баз данных."""
    MONGO = "MONGO"
    POSTGRES = "POSTGRES"

class Settings(BaseSettings):
    """Конфигурация приложения, загружаемая из .env файла."""
    DB_TYPE: DatabaseType
    DB_URL: str
    DB_NAME: str
    GRPC_PORT: int = 50051
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL: int = Field(default=300, ge=60)  # Время жизни кэша в секундах

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()