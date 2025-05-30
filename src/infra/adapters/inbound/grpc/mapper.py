import logging
from typing import Optional, List
from src.infra.adapters.inbound.grpc.py_proto import service_pb2
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.domain.models.document import Document, DocumentStatus, DocumentMetadata, DocumentVersion

class GrpcMapper:
    """Маппер для преобразования gRPC-запросов в доменные DTO и обратно."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def to_document_id_dto(request: service_pb2.GetDocumentRequest) -> DocumentIdDTO:
        """Преобразует gRPC GetDocumentRequest в DocumentIdDTO.

        Args:
            request: gRPC-запрос с ID документа.

        Returns:
            DocumentIdDTO с UUID документа.

        Raises:
            ValueError: Если ID имеет неверный формат UUID.
        """
        return DocumentIdDTO.from_string(request.id)

    @staticmethod
    def to_create_dto(request: service_pb2.CreateDocumentRequest) -> DocumentCreateDTO:
        """Преобразует gRPC CreateDocumentRequest в DocumentCreateDTO.

        Args:
            request: gRPC-запрос для создания документа.

        Returns:
            DocumentCreateDTO с данными для создания документа.
        """
        return DocumentCreateDTO(
            title=request.title,
            content=request.content,
            status=GrpcMapper._map_grpc_status_to_domain(request.status),
            metadata=DocumentMetadata(
                author=request.metadata.author,
                tags=request.metadata.tags,
                category=request.metadata.category or None
            ),
            comments=list(request.comments)
        )

    def to_update_dto(self, request: service_pb2.UpdateDocumentRequest) -> DocumentUpdateDTO:
        """Преобразует gRPC UpdateDocumentRequest в DocumentUpdateDTO.

        Args:
            request: gRPC-запрос для обновления документа.

        Returns:
            DocumentUpdateDTO с данными для обновления документа.
        """
        metadata = None
        if request.HasField('metadata'):
            if request.metadata.author.strip():
                try:
                    metadata = DocumentMetadata(
                        author=request.metadata.author,
                        tags=request.metadata.tags,
                        category=request.metadata.category or None
                    )
                except ValueError as e:
                    self.logger.warning(f"Невалидные метаданные: {str(e)}")
                    metadata = None
            else:
                self.logger.debug("Поле author в metadata пустое, metadata будет None")

        return DocumentUpdateDTO(
            title=request.title or None,
            content=request.content or None,
            status=self._map_grpc_status_to_domain(request.status) if request.status is not None else None,
            metadata=metadata,
            comments=list(request.comments) if request.comments else None
        )

    @staticmethod
    def to_list_dto(request: service_pb2.ListDocumentsRequest) -> DocumentListDTO:
        """Преобразует gRPC ListDocumentsRequest в DocumentListDTO.

        Args:
            request: gRPC-запрос для получения списка документов.

        Returns:
            DocumentListDTO с параметрами пагинации.
        """
        return DocumentListDTO(skip=request.skip, limit=request.limit)

    @staticmethod
    def to_grpc_document(document: Document) -> service_pb2.Document:
        """Преобразует доменную модель Document в gRPC Document.

        Args:
            document: Доменная модель документа.

        Returns:
            gRPC Document с данными документа.
        """
        return service_pb2.Document(
            id=str(document.id),
            title=document.title,
            content=document.content,
            status=service_pb2.DocumentStatus.Value(document.status.value.upper()),
            metadata=service_pb2.DocumentMetadata(
                author=document.metadata.author,
                tags=document.metadata.tags,
                category=document.metadata.category or ""
            ),
            comments=document.comments,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
            is_deleted=document.is_deleted
        )

    @staticmethod
    def to_grpc_list_response(documents: List[Document]) -> service_pb2.ListDocumentsResponse:
        """Преобразует список доменных моделей Document в gRPC ListDocumentsResponse.

        Args:
            documents: Список доменных моделей документов.

        Returns:
            gRPC ListDocumentsResponse с списком документов.
        """
        response = service_pb2.ListDocumentsResponse()
        for document in documents:
            response.documents.append(GrpcMapper.to_grpc_document(document))
        return response

    @staticmethod
    def to_delete_response(success: bool) -> service_pb2.DeleteDocumentResponse:
        """Преобразует результат удаления в gRPC DeleteDocumentResponse.

        Args:
            success: Успешность операции удаления.

        Returns:
            gRPC DeleteDocumentResponse с результатом.
        """
        return service_pb2.DeleteDocumentResponse(success=success)

    @staticmethod
    def to_grpc_version(version: DocumentVersion) -> service_pb2.DocumentVersion:
        """Преобразует доменную модель DocumentVersion в gRPC DocumentVersion.

        Args:
            version: Доменная модель версии документа.

        Returns:
            gRPC DocumentVersion с данными версии.
        """
        return service_pb2.DocumentVersion(
            version_id=str(version.version_id),
            content=version.content,
            metadata=service_pb2.DocumentMetadata(
                author=version.metadata.author,
                tags=version.metadata.tags,
                category=version.metadata.category or ""
            ),
            comments=version.comments,
            timestamp=version.timestamp.isoformat()
        )

    @staticmethod
    def to_grpc_versions_response(versions: List[DocumentVersion]) -> service_pb2.GetDocumentVersionsResponse:
        """Преобразует список доменных моделей DocumentVersion в gRPC GetDocumentVersionsResponse.

        Args:
            versions: Список доменных моделей версий документа.

        Returns:
            gRPC GetDocumentVersionsResponse с списком версий.
        """
        response = service_pb2.GetDocumentVersionsResponse()
        for version in versions:
            response.versions.append(GrpcMapper.to_grpc_version(version))
        return response

    @staticmethod
    def _map_grpc_status_to_domain(grpc_status: Optional[int]) -> DocumentStatus:
        """Преобразует gRPC статус в доменный DocumentStatus.

        Args:
            grpc_status: Целочисленный статус из gRPC-запроса.

        Returns:
            DocumentStatus, соответствующий gRPC статусу.

        Raises:
            ValueError: Если статус невалиден или не указан.
        """
        if grpc_status is None:
            raise ValueError("Статус документа должен быть указан")
        status_map = {
            0: DocumentStatus.DRAFT,
            1: DocumentStatus.PUBLISHED,
            2: DocumentStatus.ARCHIVED
        }
        try:
            return status_map[grpc_status]
        except KeyError:
            raise ValueError(f"Недопустимое значение статуса gRPC: {grpc_status}")