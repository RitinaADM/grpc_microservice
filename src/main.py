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

async def init_db():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing database: {settings.DB_TYPE}")
    try:
        if settings.DB_TYPE == DatabaseType.MONGO:
            client = AsyncIOMotorClient(settings.DB_URL)
            await init_beanie(database=client[settings.DB_NAME], document_models=[MongoDocument])
            logger.info("MongoDB successfully initialized")
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            logger.debug("Creating PostgreSQL async engine")
            engine = create_async_engine(settings.DB_URL, echo=True)
            logger.debug(f"Async engine created: {engine}")
            async with engine.begin() as conn:
                logger.debug("Creating tables")
                await conn.run_sync(Base.metadata.create_all)  # Только создание таблиц
            # Не закрываем engine здесь, так как он используется в DI
            logger.info("PostgreSQL successfully initialized")
        else:
            logger.error("Unsupported database type")
            raise ValueError("Unsupported database type")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

async def main():
    logger = logging.getLogger(__name__)
    logger.info("Starting application")
    await init_db()
    await serve()

if __name__ == "__main__":
    asyncio.run(main())