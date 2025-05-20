import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.infra.config.settings import settings, DatabaseType
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.infra.adapters.outbound.sql.models import Base
from sqlalchemy.ext.asyncio import create_async_engine
from src.app import serve
import logging
from src.infra.config.logging import setup_logging
from redis.asyncio import Redis


async def init_db():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing database: {settings.DB_TYPE}")
    if settings.DB_TYPE == DatabaseType.MONGO:
        client = AsyncIOMotorClient(settings.DB_URL)
        await init_beanie(database=client[settings.DB_NAME], document_models=[MongoDocument])
        logger.info("MongoDB initialized successfully")
    elif settings.DB_TYPE == DatabaseType.POSTGRES:
        engine = create_async_engine(settings.DB_URL, echo=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL initialized successfully")
    else:
        logger.error("Unsupported database type")
        raise ValueError("Неподдерживаемый тип базы данных")


async def main():
    # Инициализация базы данных
    await init_db()

    # Запуск gRPC сервера
    await serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Закрытие соединения с Redis
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        asyncio.run(redis.aclose())