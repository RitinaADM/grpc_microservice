from typing import List
from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter
from src.domain.exceptions.base import BaseAppException
import logging

class DocumentService(DocumentServicePort):
    def __init__(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter):
        self.repository = repository
        self.cache = cache
        self.logger = logging.getLogger(__name__)

    async def get_by_id(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Fetching document with ID: {id_dto.id}")
        cached_document = await self.cache.get_document(str(id_dto.id))
        if cached_document:
            self.logger.debug(f"Cache hit for document: {id_dto.id}")
            return cached_document
        try:
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(document)
            return document
        except BaseAppException as e:
            self.logger.error(f"Error fetching document: {str(e)}")
            raise

    async def create(self, data: DocumentCreateDTO) -> Document:
        self.logger.info(f"Creating new document with title: {data.title}")
        try:
            document = Document(**data.dict())
            created_document = await self.repository.create(document)
            await self.cache.set_document(created_document)
            await self.cache.set_document_versions(str(created_document.id), created_document.versions)
            await self.cache.invalidate_document_list()
            return created_document
        except BaseAppException as e:
            self.logger.error(f"Error creating document: {str(e)}")
            raise

    async def update(self, id_dto: DocumentIdDTO, data: DocumentUpdateDTO) -> Document:
        self.logger.debug(f"Updating document with ID: {id_dto.id}")
        try:
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            updated_document = await self.repository.update(id_dto.id, data)
            if not updated_document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(updated_document)
            await self.cache.set_document_versions(str(id_dto.id), updated_document.versions)
            await self.cache.invalidate_document_list()
            return updated_document
        except BaseAppException as e:
            self.logger.error(f"Error updating document: {str(e)}")
            raise

    async def delete(self, id_dto: DocumentIdDTO) -> bool:
        self.logger.info(f"Soft deleting document with ID: {id_dto.id}")
        try:
            success = await self.repository.delete(id_dto.id)
            if not success:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.invalidate_document(str(id_dto.id))
            await self.cache.invalidate_document_versions(str(id_dto.id))
            await self.cache.invalidate_document_list()
            return success
        except BaseAppException as e:
            self.logger.error(f"Error deleting document: {str(e)}")
            raise

    async def list_documents(self, params: DocumentListDTO) -> List[Document]:
        self.logger.debug(f"Listing documents with skip: {params.skip}, limit: {params.limit}")
        try:
            cached_documents = await self.cache.get_document_list(params.skip, params.limit)
            if cached_documents:
                self.logger.debug(f"Cache hit for document list skip={params.skip}, limit={params.limit}")
                return cached_documents
            documents = await self.repository.list_documents(params.skip, params.limit)
            await self.cache.set_document_list(documents, params.skip, params.limit)
            return documents
        except BaseAppException as e:
            self.logger.error(f"Error listing documents: {str(e)}")
            raise

    async def restore(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.debug(f"Restoring document with ID: {id_dto.id}")
        try:
            document = await self.repository.restore(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(document)
            await self.cache.set_document_versions(str(id_dto.id), document.versions)
            await self.cache.invalidate_document_list()
            return document
        except BaseAppException as e:
            self.logger.error(f"Error restoring document: {str(e)}")
            raise

    async def get_versions(self, id_dto: DocumentIdDTO) -> List[DocumentVersion]:
        self.logger.debug(f"Fetching versions for document with ID: {id_dto.id}")
        try:
            cached_versions = await self.cache.get_document_versions(str(id_dto.id))
            if cached_versions:
                self.logger.debug(f"Cache hit for versions: {id_dto.id}")
                return cached_versions
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document_versions(str(id_dto.id), document.versions)
            return document.versions
        except BaseAppException as e:
            self.logger.error(f"Error fetching versions: {str(e)}")
            raise

    async def get_version(self, id_dto: DocumentIdDTO, version_id: UUID) -> DocumentVersion:
        self.logger.debug(f"Fetching version {version_id} for document {id_dto.id}")
        try:
            versions = await self.get_versions(id_dto)
            for version in versions:
                if version.version_id == version_id:
                    return version
            self.logger.warning(f"Version {version_id} not found for document: {id_dto.id}")
            raise DocumentNotFoundException("Version not found")
        except BaseAppException as e:
            self.logger.error(f"Error fetching version: {str(e)}")
            raise