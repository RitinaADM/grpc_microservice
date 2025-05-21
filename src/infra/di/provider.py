from dishka import Provider, Scope, provide
from typing import AsyncGenerator
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.application.document.service import DocumentService
from src.infra.adapters.outbound.mongo.adapter import MongoDocumentAdapter
from src.infra.adapters.outbound.sql.adapter import SQLDocumentAdapter
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.infra.config.settings import settings, DatabaseType
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from redis.asyncio import Redis
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter
import logging

class AppProvider(Provider):
    """Провайдер зависимостей для DI-контейнера Dishka."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @provide(scope=Scope.APP)
    async def provide_redis(self) -> AsyncGenerator[Redis, None]:
        """Предоставляет клиент Redis."""
        self.logger.debug("Providing Redis client")
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield redis
        await redis.aclose()

    @provide(scope=Scope.APP)
    async def provide_cache(self, redis: Redis) -> RedisCacheAdapter:
        """Предоставляет адаптер кэша Redis."""
        self.logger.debug("Providing RedisCacheAdapter")
        return RedisCacheAdapter(redis)

    @provide(scope=Scope.APP)
    async def provide_session_factory(self) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
        """Предоставляет фабрику сессий для PostgreSQL."""
        self.logger.debug("Providing session factory")
        if settings.DB_TYPE == DatabaseType.POSTGRES:
            engine = create_async_engine(settings.DB_URL, echo=True, pool_size=5, max_overflow=10)
            async_session = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
            )
            yield async_session
            await engine.dispose()
        else:
            yield None

    @provide(scope=Scope.REQUEST)
    async def provide_session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
        """Предоставляет новую сессию для каждого запроса."""
        self.logger.debug("Providing new AsyncSession for request")
        if session_factory:
            async with session_factory() as session:
                yield session
        else:
            yield None

    @provide(scope=Scope.REQUEST)
    async def provide_repository(self, session: AsyncSession) -> AsyncGenerator[DocumentRepositoryPort, None]:
        """Предоставляет репозиторий в зависимости от типа базы данных."""
        self.logger.debug(f"Providing repository for DB_TYPE: {settings.DB_TYPE}")
        if settings.DB_TYPE == DatabaseType.MONGO:
            yield MongoDocumentAdapter()
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            yield SQLDocumentAdapter(session)
        else:
            raise ValueError("Неподдерживаемый тип базы данных")

    @provide(scope=Scope.REQUEST)
    async def provide_service(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter) -> DocumentServicePort:
        """Предоставляет сервис для работы с документами."""
        self.logger.debug("Providing DocumentService")
        return DocumentService(repository, cache)

    @provide(scope=Scope.REQUEST)
    async def provide_grpc_servicer(self, service: DocumentServicePort) -> DocumentServiceServicer:
        """Предоставляет gRPC сервис для обработки запросов."""
        self.logger.debug("Providing DocumentServiceServicer")
        return DocumentServiceServicer(service)