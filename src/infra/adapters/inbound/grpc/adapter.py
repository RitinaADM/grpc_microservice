import grpc
from src.domain.py_proto import service_pb2, service_pb2_grpc
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.exceptions.base import BaseAppException
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from pydantic import ValidationError
import logging
import uuid
from google.protobuf import json_format

class DocumentServiceServicer(service_pb2_grpc.DocumentServiceServicer):
    def __init__(self, service: DocumentServicePort):
        self.service = service
        self.logger = logging.getLogger(__name__)

    def _set_validation_error_details(self, context, error: ValidationError):
        details = json_format.MessageToDict(error.errors()[0]["ctx"]["error"]) if error.errors() else {"message": str(error)}
        context.set_details(json_format.MessageToJson(details))
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)

    async def GetDocument(self, request, context):
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

    async def CreateDocument(self, request, context):
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

    async def UpdateDocument(self, request, context):
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

    async def DeleteDocument(self, request, context):
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

    async def RestoreDocument(self, request, context):
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

    async def ListDocuments(self, request, context):
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