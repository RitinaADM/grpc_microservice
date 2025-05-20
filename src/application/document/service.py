from uuid import UUID
from src.domain.models.document import Document
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from typing import List
import logging
from pymongo.errors import ConnectionFailure, OperationFailure
from src.domain.exceptions.base import BaseAppException
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter


class DocumentService(DocumentServicePort):
    def __init__(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter):
        self.repository = repository
        self.cache = cache
        self.logger = logging.getLogger(__name__)

    async def get_by_id(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Fetching document with ID: {id_dto.id}")
        try:
            # Проверяем кэш
            cached_document = await self.cache.get_document(str(id_dto.id))
            if cached_document:
                self.logger.debug(f"Returning cached document: {id_dto.id}")
                return cached_document

            # Если нет в кэше, запрашиваем из базы
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()

            # Сохраняем в кэш
            await self.cache.set_document(document)
            self.logger.debug(f"Successfully fetched and cached document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def create(self, data: DocumentCreateDTO) -> Document:
        self.logger.info(f"Creating document with title: {data.title}")
        try:
            document = Document(**data.dict())
            created_document = await self.repository.create(document)
            # Сохраняем в кэш
            await self.cache.set_document(created_document)
            # Инвалидируем кэш списков
            await self.cache.invalidate_document_list()
            self.logger.debug(f"Successfully created and cached document: {created_document.id}")
            return created_document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def update(self, id_dto: DocumentIdDTO, data: DocumentUpdateDTO) -> Document:
        self.logger.info(f"Updating document with ID: {id_dto.id}, data: {data.dict(exclude_none=True)}")
        try:
            document = await self.repository.update(id_dto.id, data)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            # Обновляем кэш
            await self.cache.set_document(document)
            # Инвалидируем кэш списков
            await self.cache.invalidate_document_list()
            self.logger.debug(f"Successfully updated and cached document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def delete(self, id_dto: DocumentIdDTO) -> bool:
        self.logger.info(f"Soft deleting document with ID: {id_dto.id}")
        try:
            success = await self.repository.delete(id_dto.id)
            if not success:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            # Инвалидируем кэш документа и списков
            await self.cache.invalidate_document(str(id_dto.id))
            await self.cache.invalidate_document_list()
            self.logger.debug(f"Successfully soft deleted document: {id_dto.id}")
            return success
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def list_documents(self, params: DocumentListDTO) -> List[Document]:
        self.logger.info(f"Listing documents with skip: {params.skip}, limit: {params.limit}")
        try:
            # Проверяем кэш
            cached_documents = await self.cache.get_document_list(params.skip, params.limit)
            if cached_documents:
                self.logger.debug(f"Returning cached document list: skip={params.skip}, limit={params.limit}")
                return cached_documents

            # Если нет в кэше, запрашиваем из базы
            documents = await self.repository.list_documents(params.skip, params.limit)
            # Сохраняем в кэш
            await self.cache.set_document_list(documents, params.skip, params.limit)
            self.logger.debug(f"Successfully fetched and cached {len(documents)} documents")
            return documents
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def restore(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Restoring document with ID: {id_dto.id}")
        try:
            document = await self.repository.restore(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            # Обновляем кэш
            await self.cache.set_document(document)
            # Инвалидируем кэш списков
            await self.cache.invalidate_document_list()
            self.logger.debug(f"Successfully restored and cached document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")