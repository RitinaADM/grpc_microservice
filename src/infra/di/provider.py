from dishka import Provider, Scope, provide
from typing import AsyncGenerator
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.application.document.service import DocumentService
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.infra.adapters.outbound.mongo.adapter import MongoDocumentAdapter
from src.infra.adapters.outbound.sql.adapter import SQLDocumentAdapter
from src.infra.config.settings import settings, DatabaseType
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from redis.asyncio import Redis
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter
import logging
from logging import Logger

class AppProvider(Provider):
    """Провайдер зависимостей для DI-контейнера Dishka."""

    def __init__(self):
        super().__init__()
        self.logger: Logger = logging.getLogger(__name__)
        self.engine = None  # Для хранения AsyncEngine

    @provide(scope=Scope.APP)
    def provide_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Предоставляет фабрику сессий для PostgreSQL."""
        self.logger.debug("Инициализация async_sessionmaker для PostgreSQL")
        self.engine = create_async_engine(settings.DB_URL, echo=True)
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autobegin=False  # Prevent implicit transactions
        )

    @provide(scope=Scope.APP)
    async def provide_redis(self) -> AsyncGenerator[Redis, None]:
        """Предоставляет клиент Redis."""
        self.logger.debug("Инициализация клиента Redis")
        try:
            redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            yield redis
        finally:
            try:
                await redis.aclose()
                self.logger.debug("Клиент Redis закрыт")
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии Redis: {str(e)}")

    @provide(scope=Scope.APP)
    async def provide_cache(self, redis: Redis) -> RedisCacheAdapter:
        """Предоставляет адаптер кэша Redis."""
        self.logger.debug("Инициализация RedisCacheAdapter")
        return RedisCacheAdapter(redis)

    @provide(scope=Scope.REQUEST)
    async def provide_repository(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[
        DocumentRepositoryPort, None]:
        """Предоставляет репозиторий в зависимости от типа базы данных, создавая новую сессию для PostgreSQL."""
        self.logger.debug(f"Предоставление репозитория для DB_TYPE: {settings.DB_TYPE}")
        if settings.DB_TYPE == DatabaseType.MONGO:
            yield MongoDocumentAdapter()
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            async with session_factory() as session:
                self.logger.debug(f"Сессия создана для репозитория: id={id(session)}")
                yield SQLDocumentAdapter(session)
                self.logger.debug(f"Сессия закрывается: id={id(session)}")
                if session.in_transaction():
                    self.logger.warning(f"Сессия id={id(session)} все еще в транзакции, выполняется rollback")
                    await session.rollback()
        else:
            self.logger.error(f"Неподдерживаемый тип базы данных: {settings.DB_TYPE}")
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
        if self.engine:
            await self.engine.dispose()
            self.logger.debug("Database engine disposed")