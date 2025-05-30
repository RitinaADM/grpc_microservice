import logging
from typing import List
from src.infra.adapters.inbound.grpc.py_proto import service_pb2
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.domain.models.document import Document, DocumentStatus, DocumentVersion
from src.domain.ports.outbound.mappers.base import BaseMapper

class GrpcMapper(BaseMapper[Document]):
    """Маппер для преобразования между gRPC-сообщениями и доменными объектами."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def to_document_id_dto(self, request: service_pb2.GetDocumentRequest) -> DocumentIdDTO:
        """Преобразует gRPC GetDocumentRequest в DocumentIdDTO."""
        return DocumentIdDTO.from_string(request.id)

    def to_create_dto(self, request: service_pb2.CreateDocumentRequest) -> DocumentCreateDTO:
        """Преобразует gRPC CreateDocumentRequest в DocumentCreateDTO."""
        return DocumentCreateDTO(
            title=request.title,
            content=request.content,
            status=self._map_grpc_status_to_domain(request.status),
            author=request.author,
            tags=list(request.tags),
            category=request.category or None,
            comments=list(request.comments)
        )

    def to_update_dto(self, request: service_pb2.UpdateDocumentRequest) -> DocumentUpdateDTO:
        """Преобразует gRPC UpdateDocumentRequest в DocumentUpdateDTO."""
        return DocumentUpdateDTO(
            title=request.title or None,
            content=request.content or None,
            status=self._map_grpc_status_to_domain(request.status) if request.status else None,
            author=request.author or None,
            tags=list(request.tags) if request.tags else None,
            category=request.category or None,
            comments=list(request.comments) if request.comments else None
        )

    def to_list_dto(self, request: service_pb2.ListDocumentsRequest) -> DocumentListDTO:
        """Преобразует gRPC ListDocumentsRequest в DocumentListDTO."""
        return DocumentListDTO(skip=request.skip, limit=request.limit)

    def to_grpc_document(self, document: Document) -> service_pb2.Document:
        """Преобразует доменный Document в gRPC Document."""
        return service_pb2.Document(
            id=self._serialize_uuid(document.id),
            title=document.title,
            content=document.content,
            status=service_pb2.DocumentStatus.Value(document.status.value.upper()),
            author=document.author,
            tags=document.tags,
            category=document.category or "",
            comments=document.comments,
            created_at=self._serialize_datetime(document.created_at),
            updated_at=self._serialize_datetime(document.updated_at),
            is_deleted=document.is_deleted
        )

    def to_grpc_list_response(self, documents: List[Document]) -> service_pb2.ListDocumentsResponse:
        """Преобразует список доменных Document в gRPC ListDocumentsResponse."""
        response = service_pb2.ListDocumentsResponse()
        response.documents.extend([self.to_grpc_document(doc) for doc in documents])
        return response

    def to_delete_response(self, success: bool) -> service_pb2.DeleteDocumentResponse:
        """Преобразует результат удаления в gRPC DeleteDocumentResponse."""
        return service_pb2.DeleteDocumentResponse(success=success)

    def to_grpc_version(self, version: DocumentVersion) -> service_pb2.DocumentVersion:
        """Преобразует доменную DocumentVersion в gRPC DocumentVersion."""
        return service_pb2.DocumentVersion(
            version_id=self._serialize_uuid(version.version_id),
            document=self.to_grpc_document(version.document),
            timestamp=self._serialize_datetime(version.timestamp)
        )

    def to_grpc_versions_response(self, versions: List[DocumentVersion]) -> service_pb2.GetDocumentVersionsResponse:
        """Преобразует список доменных DocumentVersion в gRPC GetDocumentVersionsResponse."""
        response = service_pb2.GetDocumentVersionsResponse()
        response.versions.extend([self.to_grpc_version(v) for v in versions])
        return response

    def to_storage(self, obj: Document) -> service_pb2.Document:
        """Сериализует Document в gRPC Document."""
        return self.to_grpc_document(obj)

    def from_storage(self, data: service_pb2.Document) -> Document:
        """Десериализует gRPC Document в доменный Document."""
        return Document(
            id=self._deserialize_uuid(data.id),
            title=data.title,
            content=data.content,
            status=self._map_grpc_status_to_domain(data.status),
            author=data.author,
            tags=list(data.tags),
            category=data.category or None,
            comments=list(data.comments),
            created_at=self._deserialize_datetime(data.created_at),
            updated_at=self._deserialize_datetime(data.updated_at),
            is_deleted=data.is_deleted
        )

    @staticmethod
    def _map_grpc_status_to_domain(grpc_status: int) -> DocumentStatus:
        """Преобразует gRPC статус в доменный DocumentStatus."""
        status_map = {
            0: DocumentStatus.DRAFT,
            1: DocumentStatus.PUBLISHED,
            2: DocumentStatus.ARCHIVED
        }
        try:
            return status_map[grpc_status]
        except KeyError:
            raise ValueError(f"Invalid gRPC status: {grpc_status}")