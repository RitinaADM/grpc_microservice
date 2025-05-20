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

class AppProvider(Provider):
    """Провайдер зависимостей для DI-контейнера Dishka."""

    @provide(scope=Scope.APP)
    async def provide_repository(self) -> AsyncGenerator[DocumentRepositoryPort, None]:
        """Предоставляет репозиторий в зависимости от типа базы данных."""
        if settings.DB_TYPE == DatabaseType.MONGO:
            yield MongoDocumentAdapter()
        elif settings.DB_TYPE == DatabaseType.POSTGRES:
            engine = create_async_engine(settings.DB_URL, echo=True)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            session = async_session()
            yield SQLDocumentAdapter(session)
        else:
            raise ValueError("Неподдерживаемый тип базы данных")

    @provide(scope=Scope.APP)
    async def provide_service(self, repository: DocumentRepositoryPort) -> DocumentServicePort:
        """Предоставляет сервис для работы с документами."""
        return DocumentService(repository)

    @provide(scope=Scope.APP)
    async def provide_grpc_servicer(self, service: DocumentServicePort) -> DocumentServiceServicer:
        """Предоставляет gRPC сервис для обработки запросов."""
        return DocumentServiceServicer(service)