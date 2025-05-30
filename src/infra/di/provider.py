from dishka import Provider, Scope, provide
from typing import AsyncGenerator, Optional
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.application.document.service import DocumentService
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.infra.adapters.outbound.mongo.adapter import MongoDocumentAdapter
from src.infra.adapters.outbound.sql.adapter import SQLDocumentAdapter
from src.infra.config.settings import settings, DatabaseType
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from redis.asyncio import Redis, ConnectionPool
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter
from src.infra.adapters.outbound.redis.mapper import RedisMapper
import logging
from logging import Logger

class AppProvider(Provider):
    """Провайдер зависимостей для DI-контейнера Dishka."""

    def __init__(self):
        super().__init__()
        self.logger: Logger = logging.getLogger(__name__)
        self.engine = None  # Для хранения AsyncEngine

    @provide(scope=Scope.APP)
    def provide_session_factory(self) -> Optional[async_sessionmaker[AsyncSession]]:
        """Предоставляет фабрику сессий для PostgreSQL."""
        if settings.DB_TYPE == DatabaseType.POSTGRES:
            self.logger.debug("Инициализация async_sessionmaker для PostgreSQL")
            self.engine = create_async_engine(settings.DB_URL, echo=True)
            return async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autobegin=False
            )
        elif settings.DB_TYPE == DatabaseType.MONGO:
            self.logger.debug("No session factory needed for MongoDB")
            return None
        else:
            self.logger.error("Неподдерживаемый тип базы данных")
            raise ValueError("Неподдерживаемый тип базы данных")

    @provide(scope=Scope.APP)
    async def provide_redis(self) -> AsyncGenerator[Redis, None]:
        """Предоставляет клиент Redis с пулом соединений."""
        self.logger.debug("Инициализация клиента Redis")
        pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
        redis = Redis(connection_pool=pool)
        try:
            yield redis
        finally:
            await redis.aclose()
            await pool.disconnect()
            self.logger.debug("Клиент Redis закрыт")

    @provide(scope=Scope.APP)
    async def provide_cache(self, redis: Redis) -> RedisCacheAdapter:
        """Предоставляет адаптер кэша Redis."""
        self.logger.debug("Инициализация RedisCacheAdapter")
        return RedisCacheAdapter(redis)

    @provide(scope=Scope.REQUEST)
    async def provide_repository(self, session_factory: Optional[async_sessionmaker[AsyncSession]]) -> DocumentRepositoryPort:
        """Предоставляет репозиторий в зависимости от типа базы данных."""
        self.logger.debug(f"Предоставление репозитория для DB_TYPE: {settings.DB_TYPE}")
        if settings.DB_TYPE == DatabaseType.MONGO:
            return MongoDocumentAdapter()
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            if session_factory is None:
                self.logger.error("Session factory is required for PostgreSQL")
                raise ValueError("Session factory is required for PostgreSQL")
            self.logger.debug("Создание SQLDocumentAdapter с session_factory")
            return SQLDocumentAdapter(session_factory)
        else:
            self.logger.error("Неподдерживаемый тип базы данных")
            raise ValueError("Неподдерживаемый тип базы данных")

    @provide(scope=Scope.REQUEST)
    async def provide_service(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter) -> DocumentServicePort:
        """Предоставляет сервис для работы с документами."""
        self.logger.debug("Инициализация DocumentService")
        return DocumentService(repository, cache)

    @provide(scope=Scope.REQUEST)
    async def provide_grpc_servicer(self, service: DocumentServicePort) -> DocumentServiceServicer:
        """Предоставляет gRPC сервис для обработки запросов."""
        self.logger.debug("Инициализация DocumentServiceServicer")
        return DocumentServiceServicer(service)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает AsyncEngine при завершении работы контейнера."""
        self.logger.debug("Closing DI container")
        if self.engine:
            await self.engine.dispose()
            self.logger.debug("Database engine disposed")