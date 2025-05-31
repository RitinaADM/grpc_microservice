from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseType(str, Enum):
    MONGO = "MONGO"
    POSTGRES = "POSTGRES"

class Settings(BaseSettings):
    DB_TYPE: DatabaseType = DatabaseType.MONGO
    DB_NAME: str = "microservice_db"
    MONGO_URL: str = "mongodb://mongo:27017"
    POSTGRES_URL: str = "postgresql+asyncpg://user:password@postgres:5432/microservice_db"
    REDIS_URL: str = "redis://redis:6379/0"
    GRPC_PORT: int = 50051
    LOG_LEVEL: str = "INFO"
    CACHE_TTL: int = 300

    @property
    def DB_URL(self) -> str:
        if self.DB_TYPE == DatabaseType.MONGO:
            return f"{self.MONGO_URL}/{self.DB_NAME}"
        return self.POSTGRES_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорировать лишние поля
    )

settings = Settings()