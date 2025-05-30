import logging
from typing import List
from src.infra.adapters.inbound.grpc.py_proto import service_pb2
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.domain.models.document import Document, DocumentStatus, DocumentVersion
from datetime import datetime

class GrpcMapper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def to_document_id_dto(request: service_pb2.GetDocumentRequest) -> DocumentIdDTO:
        return DocumentIdDTO.from_string(request.id)

    @staticmethod
    def to_create_dto(request: service_pb2.CreateDocumentRequest) -> DocumentCreateDTO:
        return DocumentCreateDTO(
            title=request.title,
            content=request.content,
            status=GrpcMapper._map_grpc_status_to_domain(request.status),
            author=request.author,
            tags=list(request.tags),
            category=request.category or None,
            comments=list(request.comments)
        )

    @staticmethod
    def to_update_dto(request: service_pb2.UpdateDocumentRequest) -> DocumentUpdateDTO:
        return DocumentUpdateDTO(
            title=request.title or None,
            content=request.content or None,
            status=GrpcMapper._map_grpc_status_to_domain(request.status) if request.status else None,
            author=request.author or None,
            tags=list(request.tags) if request.tags else None,
            category=request.category or None,
            comments=list(request.comments) if request.comments else None
        )

    @staticmethod
    def to_list_dto(request: service_pb2.ListDocumentsRequest) -> DocumentListDTO:
        return DocumentListDTO(skip=request.skip, limit=request.limit)

    @staticmethod
    def to_grpc_document(document: Document) -> service_pb2.Document:
        return service_pb2.Document(
            id=str(document.id),
            title=document.title,
            content=document.content,
            status=service_pb2.DocumentStatus.Value(document.status.value.upper()),
            author=document.author,
            tags=document.tags,
            category=document.category or "",
            comments=document.comments,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
            is_deleted=document.is_deleted
        )

    @staticmethod
    def to_grpc_list_response(documents: List[Document]) -> service_pb2.ListDocumentsResponse:
        response = service_pb2.ListDocumentsResponse()
        response.documents.extend([GrpcMapper.to_grpc_document(doc) for doc in documents])
        return response

    @staticmethod
    def to_delete_response(success: bool) -> service_pb2.DeleteDocumentResponse:
        return service_pb2.DeleteDocumentResponse(success=success)

    @staticmethod
    def to_grpc_version(version: DocumentVersion) -> service_pb2.DocumentVersion:
        return service_pb2.DocumentVersion(
            version_id=str(version.version_id),
            document=GrpcMapper.to_grpc_document(version.document),
            timestamp=version.timestamp.isoformat()
        )

    @staticmethod
    def to_grpc_versions_response(versions: List[DocumentVersion]) -> service_pb2.GetDocumentVersionsResponse:
        response = service_pb2.GetDocumentVersionsResponse()
        response.versions.extend([GrpcMapper.to_grpc_version(v) for v in versions])
        return response

    @staticmethod
    def _map_grpc_status_to_domain(grpc_status: int) -> DocumentStatus:
        status_map = {
            0: DocumentStatus.DRAFT,
            1: DocumentStatus.PUBLISHED,
            2: DocumentStatus.ARCHIVED
        }
        try:
            return status_map[grpc_status]
        except KeyError:
            raise ValueError(f"Invalid gRPC status: {grpc_status}")