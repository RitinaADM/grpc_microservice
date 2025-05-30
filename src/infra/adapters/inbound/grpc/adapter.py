import asyncio
import logging
import uuid
import grpc
from grpc.aio import ServicerContext
from pydantic import ValidationError
from src.infra.adapters.inbound.grpc.py_proto import service_pb2_grpc, service_pb2
from src.infra.adapters.inbound.grpc.mapper import GrpcMapper
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.exceptions.base import BaseAppException
from typing import TypeVar, Type
from uuid import UUID

T = TypeVar('T')

class DocumentServiceServicer(service_pb2_grpc.DocumentServiceServicer):
    """gRPC-сервис для управления документами, реализующий DocumentServiceServicer из Protobuf."""

    def __init__(self, service: DocumentServicePort):
        """Инициализирует сервис с внедренной зависимостью DocumentServicePort.

        Args:
            service: Сервис для выполнения бизнес-логики с документами.
        """
        self.service: DocumentServicePort = service
        self.mapper = GrpcMapper()
        self.logger = logging.getLogger(__name__)

    def _set_validation_error_details(self, context: ServicerContext, error: ValidationError) -> None:
        """Устанавливает детали ошибки валидации в gRPC-контексте.

        Args:
            context: gRPC-контекст для установки статуса и деталей.
            error: Ошибка валидации Pydantic.
        """
        if error.errors():
            first_error = error.errors()[0]
            field = ".".join(str(loc) for loc in first_error["loc"])
            message = first_error["msg"]
            details = f"Ошибка валидации для поля '{field}': {message}"
        else:
            details = str(error)
        context.set_details(details)
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)

    async def _handle_grpc_errors(self, func, context: ServicerContext, request_id: str, response_type: Type[T]) -> T:
        """Обрабатывает исключения в gRPC-методах и преобразует их в соответствующие gRPC-статусы.

        Args:
            func: Асинхронная функция для выполнения бизнес-логики.
            context: gRPC-контекст для установки статуса и деталей ошибки.
            request_id: Уникальный идентификатор запроса для логирования.
            response_type: Тип возвращаемого gRPC-ответа.

        Returns:
            Результат выполнения функции или пустой объект response_type при ошибке.
        """
        try:
            return await func()
        except ValidationError as e:
            self.logger.error(f"Ошибка валидации: {str(e)}", extra={"request_id": request_id})
            self._set_validation_error_details(context, e)
            return response_type()
        except ValueError as e:
            self.logger.error(f"Некорректный ввод: {str(e)}", extra={"request_id": request_id})
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return response_type()
        except DocumentNotFoundException as e:
            self.logger.warning(f"Операция не выполнена: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return response_type()
        except BaseAppException as e:
            self.logger.error(f"Ошибка базы данных: {str(e)}", extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return response_type()
        except Exception as e:
            self.logger.error(f"Непредвиденная ошибка: {str(e)}", exc_info=True, extra={"request_id": request_id})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Внутренняя ошибка сервера")
            return response_type()

    async def GetDocument(self, request: service_pb2.GetDocumentRequest, context: ServicerContext) -> service_pb2.GetDocumentResponse:
        """Получает документ по ID через gRPC.

        Args:
            request: gRPC-запрос с ID документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC GetDocumentResponse с данными документа.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос GetDocument для ID: {request.id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            document = await self.service.get_by_id(id_dto)
            return service_pb2.GetDocumentResponse(document=self.mapper.to_grpc_document(document))
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.GetDocumentResponse)

    async def CreateDocument(self, request: service_pb2.CreateDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Создает новый документ через gRPC.

        Args:
            request: gRPC-запрос с данными для создания документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC Document с данными созданного документа.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос CreateDocument: {request.title}", extra={"request_id": request_id})
        async def handle():
            data = self.mapper.to_create_dto(request)
            document = await self.service.create(data)
            return self.mapper.to_grpc_document(document)
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.Document)

    async def UpdateDocument(self, request: service_pb2.UpdateDocumentRequest, context: ServicerContext) -> service_pb2.UpdateDocumentResponse:
        """Обновляет существующий документ через gRPC.

        Args:
            request: gRPC-запрос с ID и данными для обновления документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC UpdateDocumentResponse с данными обновленного документа.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос UpdateDocument для ID: {request.id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            data = self.mapper.to_update_dto(request)
            document = await self.service.update(id_dto, data)
            return service_pb2.UpdateDocumentResponse(document=self.mapper.to_grpc_document(document))
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.UpdateDocumentResponse)

    async def DeleteDocument(self, request: service_pb2.DeleteDocumentRequest, context: ServicerContext) -> service_pb2.DeleteDocumentResponse:
        """Удаляет документ по ID через gRPC (мягкое удаление).

        Args:
            request: gRPC-запрос с ID документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC DeleteDocumentResponse с результатом операции.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос DeleteDocument для ID: {request.id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            success = await self.service.delete(id_dto)
            return self.mapper.to_delete_response(success)
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.DeleteDocumentResponse)

    async def RestoreDocument(self, request: service_pb2.RestoreDocumentRequest, context: ServicerContext) -> service_pb2.Document:
        """Восстанавливает удаленный документ по ID через gRPC.

        Args:
            request: gRPC-запрос с ID документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC Document с данными восстановленного документа.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос RestoreDocument для ID: {request.id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            document = await self.service.restore(id_dto)
            return self.mapper.to_grpc_document(document)
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.Document)

    async def ListDocuments(self, request: service_pb2.ListDocumentsRequest, context: ServicerContext) -> service_pb2.ListDocumentsResponse:
        """Получает список документов с пагинацией через gRPC.

        Args:
            request: gRPC-запрос с параметрами пагинации (skip, limit).
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC ListDocumentsResponse со списком документов.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос ListDocuments с skip: {request.skip}, limit: {request.limit}",
                         extra={"request_id": request_id})
        self.logger.debug(f"Event loop: {asyncio.get_running_loop()}")

        async def handle():
            self.logger.info("Обрабатываем ListDocuments")
            params = self.mapper.to_list_dto(request)
            documents = await self.service.list_documents(params)
            return self.mapper.to_grpc_list_response(documents)

        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.ListDocumentsResponse)

    async def GetDocumentVersions(self, request: service_pb2.GetDocumentVersionsRequest, context: ServicerContext) -> service_pb2.GetDocumentVersionsResponse:
        """Получает список версий документа по ID через gRPC.

        Args:
            request: gRPC-запрос с ID документа.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC GetDocumentVersionsResponse со списком версий документа.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос GetDocumentVersions для ID: {request.id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            versions = await self.service.get_versions(id_dto)
            return self.mapper.to_grpc_versions_response(versions)
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.GetDocumentVersionsResponse)

    async def GetDocumentVersion(self, request: service_pb2.GetDocumentVersionRequest, context: ServicerContext) -> service_pb2.DocumentVersion:
        """Получает конкретную версию документа по ID документа и ID версии через gRPC.

        Args:
            request: gRPC-запрос с ID документа и ID версии.
            context: gRPC-контекст для обработки ошибок.

        Returns:
            gRPC DocumentVersion с данными версии.
        """
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"Получен запрос GetDocumentVersion для ID: {request.id}, version_id: {request.version_id}", extra={"request_id": request_id})
        async def handle():
            id_dto = self.mapper.to_document_id_dto(request)
            version_id = UUID(request.version_id)
            version = await self.service.get_version(id_dto, version_id)
            return self.mapper.to_grpc_version(version)
        return await self._handle_grpc_errors(handle, context, request_id, service_pb2.DocumentVersion)