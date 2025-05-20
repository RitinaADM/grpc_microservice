from dishka import Provider, Scope, provide
from typing import AsyncGenerator
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.application.document.service import DocumentService
from src.infra.adapters.outbound.mongo.adapter import MongoDocumentAdapter
from src.infra.adapters.outbound.sql.adapter import SQLDocumentAdapter
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.infra.config.settings import settings, DatabaseType
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter

class AppProvider(Provider):
    """Провайдер зависимостей для DI-контейнера Dishka."""

    @provide(scope=Scope.APP)
    async def provide_redis(self) -> AsyncGenerator[Redis, None]:
        """Предоставляет клиент Redis."""
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield redis
        await redis.aclose()

    @provide(scope=Scope.APP)
    async def provide_cache(self, redis: Redis) -> RedisCacheAdapter:
        """Предоставляет адаптер кэша Redis."""
        return RedisCacheAdapter(redis)

    @provide(scope=Scope.APP)
    async def provide_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Предоставляет пул сессий для PostgreSQL."""
        if settings.DB_TYPE == DatabaseType.POSTGRES:
            engine = create_async_engine(settings.DB_URL, echo=True, pool_size=5, max_overflow=10)
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
            )
            async with async_session() as session:
                yield session
            await engine.dispose()
        else:
            yield None

    @provide(scope=Scope.APP)
    async def provide_repository(self, session: AsyncSession) -> AsyncGenerator[DocumentRepositoryPort, None]:
        """Предоставляет репозиторий в зависимости от типа базы данных."""
        if settings.DB_TYPE == DatabaseType.MONGO:
            yield MongoDocumentAdapter()
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            yield SQLDocumentAdapter(session)
        else:
            raise ValueError("Неподдерживаемый тип базы данных")

    @provide(scope=Scope.APP)
    async def provide_service(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter) -> DocumentServicePort:
        """Предоставляет сервис для работы с документами."""
        return DocumentService(repository, cache)

    @provide(scope=Scope.APP)
    async def provide_grpc_servicer(self, service: DocumentServicePort) -> DocumentServiceServicer:
        """Предоставляет gRPC сервис для обработки запросов."""
        return DocumentServiceServicer(service)