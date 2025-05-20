import logging

import grpc
from grpc.aio import ServicerContext
from logging import Logger
from pydantic import ValidationError
from typing import Optional
import uuid
from src.domain.py_proto import service_pb2, service_pb2_grpc
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.exceptions.base import BaseAppException
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO

class DocumentServiceServicer(service_pb2_grpc.DocumentServiceServicer):
    """gRPC сервис для обработки запросов к документам."""

    def __init__(self, service: DocumentServicePort):
        """Инициализация сервиса с внедрением зависимости."""
        self.service: DocumentServicePort = service
        self.logger: Logger = logging.getLogger(__name__)

    def _set_validation_error_details(self, context: ServicerContext, error: ValidationError) -> None:
        """Устанавливает детали ошибки валидации для gRPC ответа."""
        if error.errors():
            first_error = error.errors()[0]
            field = ".".join(str(loc) for loc in first_error["loc"])
            message = first_error["msg"]
            details = f"Validation error for field '{field}': {message}"
        else:
            details = str(error)
        context.set_details(details)
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)

    async def GetDocument(self, request: service_pb2.GetDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Получение документа по ID."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received GetDocument request for ID: {request.id}", extra={"request_id": request_id})
        try:
            id_dto = DocumentIdDTO.from_string(request.id)
            document = await self.service.get_by_id(id_dto)
            self.logger.debug(f"Returning document: {document.id}", extra={"request_id": request_id})
            return service_pb2.Document(
                id=str(document.id),
                title=document.title,
                content=document.content,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat(),
                is_deleted=document.is_deleted
            )
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.Document()
        except ValueError as e:
            self.logger.error(f"Invalid UUID: {str(e)}", extra={"request_id": request_id})
            context.set_details("Invalid document ID format")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return service_pb2.Document()
        except DocumentNotFoundException as e:
            self.logger.warning(f"GetDocument failed: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return service_pb2.Document()
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.Document()
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.Document()

    async def CreateDocument(self, request: service_pb2.CreateDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Создание нового документа."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received CreateDocument request: {request.title}", extra={"request_id": request_id})
        try:
            data = DocumentCreateDTO(title=request.title, content=request.content)
            document = await self.service.create(data)
            self.logger.debug(f"Created document: {document.id}", extra={"request_id": request_id})
            return service_pb2.Document(
                id=str(document.id),
                title=document.title,
                content=document.content,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat(),
                is_deleted=document.is_deleted
            )
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.Document()
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.Document()
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.Document()

    async def UpdateDocument(self, request: service_pb2.UpdateDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Обновление документа по ID."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received UpdateDocument request for ID: {request.id}", extra={"request_id": request_id})
        try:
            id_dto = DocumentIdDTO.from_string(request.id)
            data = DocumentUpdateDTO(title=request.title or None, content=request.content or None)
            document = await self.service.update(id_dto, data)
            self.logger.debug(f"Updated document: {document.id}", extra={"request_id": request_id})
            return service_pb2.Document(
                id=str(document.id),
                title=document.title,
                content=document.content,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat(),
                is_deleted=document.is_deleted
            )
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.Document()
        except ValueError as e:
            self.logger.error(f"Invalid UUID: {str(e)}", extra={"request_id": request_id})
            context.set_details("Invalid document ID format")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return service_pb2.Document()
        except DocumentNotFoundException as e:
            self.logger.warning(f"UpdateDocument failed: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return service_pb2.Document()
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.Document()
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.Document()

    async def DeleteDocument(self, request: service_pb2.DeleteDocumentRequest, context: ServicerContext) -> service_pb2.DeleteDocumentResponse:
        """Мягкое удаление документа по ID."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received DeleteDocument request for ID: {request.id}", extra={"request_id": request_id})
        try:
            id_dto = DocumentIdDTO.from_string(request.id)
            success = await self.service.delete(id_dto)
            self.logger.debug(f"DeleteDocument success: {success}", extra={"request_id": request_id})
            return service_pb2.DeleteDocumentResponse(success=success)
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.DeleteDocumentResponse(success=False)
        except ValueError as e:
            self.logger.error(f"Invalid UUID: {str(e)}", extra={"request_id": request_id})
            context.set_details("Invalid document ID format")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return service_pb2.DeleteDocumentResponse(success=False)
        except DocumentNotFoundException as e:
            self.logger.warning(f"DeleteDocument failed: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return service_pb2.DeleteDocumentResponse(success=False)
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.DeleteDocumentResponse(success=False)
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.DeleteDocumentResponse(success=False)

    async def RestoreDocument(self, request: service_pb2.GetDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Восстановление удаленного документа по ID."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received RestoreDocument request for ID: {request.id}", extra={"request_id": request_id})
        try:
            id_dto = DocumentIdDTO.from_string(request.id)
            document = await self.service.restore(id_dto)
            self.logger.debug(f"Restored document: {document.id}", extra={"request_id": request_id})
            return service_pb2.Document(
                id=str(document.id),
                title=document.title,
                content=document.content,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat(),
                is_deleted=document.is_deleted
            )
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.Document()
        except ValueError as e:
            self.logger.error(f"Invalid UUID: {str(e)}", extra={"request_id": request_id})
            context.set_details("Invalid document ID format")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return service_pb2.Document()
        except DocumentNotFoundException as e:
            self.logger.warning(f"RestoreDocument failed: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return service_pb2.Document()
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.Document()
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.Document()

    async def ListDocuments(self, request: service_pb2.ListDocumentsRequest, context: ServicerContext) -> service_pb2.ListDocumentsResponse:
        """Получение списка документов с пагинацией."""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Received ListDocuments request with skip: {request.skip}, limit: {request.limit}", extra={"request_id": request_id})
        try:
            params = DocumentListDTO(skip=request.skip, limit=request.limit)
            documents = await self.service.list_documents(params)
            self.logger.debug(f"Returning {len(documents)} documents", extra={"request_id": request_id})
            response = service_pb2.ListDocumentsResponse()
            for document in documents:
                response.documents.append(
                    service_pb2.Document(
                        id=str(document.id),
                        title=document.title,
                        content=document.content,
                        created_at=document.created_at.isoformat(),
                        updated_at=document.updated_at.isoformat(),
                        is_deleted=document.is_deleted
                    )
                )
            return response
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return service_pb2.ListDocumentsResponse()
        except BaseAppException as e:
            self.logger.error(f"Database error: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.ListDocumentsResponse()
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return service_pb2.ListDocumentsResponse()