from typing import List
from uuid import UUID
from src.domain.models.document import Document, DocumentVersion
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.exceptions.document import DocumentNotFoundException
from src.application.document.dto import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.infra.adapters.outbound.redis.adapter import RedisCacheAdapter
from src.domain.exceptions.base import BaseAppException
import logging

class DocumentService(DocumentServicePort):
    def __init__(self, repository: DocumentRepositoryPort, cache: RedisCacheAdapter):
        self.repository = repository
        self.cache = cache
        self.logger = logging.getLogger(__name__)

    async def get_by_id(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Получение документа с ID: {id_dto.id}")
        cached_document = await self.cache.get_document(str(id_dto.id))
        if cached_document:
            self.logger.debug(f"Кэш-попадание для документа: {id_dto.id}")
            return cached_document
        try:
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(document)
            return document
        except BaseAppException as e:
            self.logger.error(f"Ошибка при получении документа: {str(e)}")
            raise

    async def create(self, data: DocumentCreateDTO) -> Document:
        self.logger.info(f"Создание нового документа с заголовком: {data.title}")
        try:
            document = Document(**data.model_dump())
            created_document = await self.repository.save(document)
            await self.cache.set_document(created_document)
            await self.cache.set_document_versions(str(created_document.id), created_document.versions)
            await self.cache.invalidate_document_list()
            return created_document
        except BaseAppException as e:
            self.logger.error(f"Ошибка при создании документа: {str(e)}")
            raise

    async def update(self, id_dto: DocumentIdDTO, data: DocumentUpdateDTO) -> Document:
        self.logger.debug(f"Обновление документа с ID: {id_dto.id}")
        try:
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            updated_document = await self.repository.update(id_dto.id, data)
            if not updated_document:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(updated_document)
            await self.cache.set_document_versions(str(id_dto.id), updated_document.versions)
            await self.cache.invalidate_document_list()
            return updated_document
        except BaseAppException as e:
            self.logger.error(f"Ошибка при обновлении документа: {str(e)}")
            raise

    async def delete(self, id_dto: DocumentIdDTO) -> bool:
        self.logger.info(f"Мягкое удаление документа с ID: {id_dto.id}")
        try:
            success = await self.repository.delete(id_dto.id)
            if not success:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.invalidate_document(str(id_dto.id))
            await self.cache.invalidate_document_versions(str(id_dto.id))
            await self.cache.invalidate_document_list()
            return success
        except BaseAppException as e:
            self.logger.error(f"Ошибка при удалении документа: {str(e)}")
            raise

    async def list_documents(self, params: DocumentListDTO) -> List[Document]:
        self.logger.debug(f"Получение списка документов с пропуском: {params.skip}, лимитом: {params.limit}")
        try:
            cached_documents = await self.cache.get_document_list(params.skip, params.limit)
            if cached_documents:
                self.logger.debug(f"Кэш-попадание для списка документов с пропуском={params.skip}, лимитом={params.limit}")
                return cached_documents
            documents = await self.repository.list_documents(params.skip, params.limit)
            await self.cache.set_document_list(documents, params.skip, params.limit)
            return documents
        except BaseAppException as e:
            self.logger.error(f"Ошибка при получении списка документов: {str(e)}")
            raise

    async def restore(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.debug(f"Восстановление документа с ID: {id_dto.id}")
        try:
            document = await self.repository.restore(id_dto.id)
            if not document:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document(document)
            await self.cache.set_document_versions(str(id_dto.id), document.versions)
            await self.cache.invalidate_document_list()
            return document
        except BaseAppException as e:
            self.logger.error(f"Ошибка при восстановлении документа: {str(e)}")
            raise

    async def get_versions(self, id_dto: DocumentIdDTO) -> List[DocumentVersion]:
        self.logger.debug(f"Получение версий для документа с ID: {id_dto.id}")
        try:
            cached_versions = await self.cache.get_document_versions(str(id_dto.id))
            if cached_versions:
                self.logger.debug(f"Кэш-попадание для версий документа: {id_dto.id}")
                return cached_versions
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Документ не найден: {id_dto.id}")
                raise DocumentNotFoundException()
            await self.cache.set_document_versions(str(id_dto.id), document.versions)
            return document.versions
        except BaseAppException as e:
            self.logger.error(f"Ошибка при получении версий документа: {str(e)}")
            raise

    async def get_version(self, id_dto: DocumentIdDTO, version_id: UUID) -> DocumentVersion:
        self.logger.debug(f"Получение версии {version_id} для документа {id_dto.id}")
        try:
            versions = await self.get_versions(id_dto)
            for version in versions:
                if version.version_id == version_id:
                    return version
            self.logger.warning(f"Версия {version_id} не найдена для документа: {id_dto.id}")
            raise DocumentNotFoundException("Версия не найдена")
        except BaseAppException as e:
            self.logger.error(f"Ошибка при получении версии документа: {str(e)}")
            raise