import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logging import Logger
from src.domain.models.document import Document, DocumentVersion
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.dtos.document import DocumentUpdateDTO
from src.infra.adapters.outbound.mongo.mapper import MongoMapper

class MongoDocumentAdapter(DocumentRepositoryPort):
    def __init__(self):
        self.logger: Logger = logging.getLogger(__name__)
        self.mapper = MongoMapper()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def get_by_id(self, id: UUID) -> Optional[Document]:
        """
        Получает документ из MongoDB по его UUID.

        Args:
            id: UUID документа.

        Returns:
            Document: Доменная модель документа, если найден.
            None: Если документ не найден или помечен как удаленный.
        """
        self.logger.debug(f"Получение документа из MongoDB с ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
        return self.mapper.to_domain_document(mongo_doc) if mongo_doc else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def create(self, document: Document) -> Document:
        """
        Создает новый документ в MongoDB.

        Args:
            document: Доменная модель документа.

        Returns:
            Document: Созданная доменная модель документа.
        """
        self.logger.debug(f"Создание документа в MongoDB: {document.id}")
        mongo_doc = self.mapper.to_mongo_document(document)
        await mongo_doc.insert()
        return document

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        """
        Обновляет документ в MongoDB по его UUID.

        Args:
            id: UUID документа.
            data: DTO с данными для обновления.

        Returns:
            Document: Обновленная доменная модель документа, если найден.
            None: Если документ не найден или помечен как удаленный.
        """
        self.logger.debug(f"Обновление документа в MongoDB с ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
        if mongo_doc:
            # Сохраняем текущую версию документа
            try:
                current_version = DocumentVersion(
                    version_id=uuid4(),
                    content=mongo_doc.content,
                    metadata=mongo_doc.metadata,
                    comments=mongo_doc.comments,
                    timestamp=datetime.utcnow()
                )
                mongo_doc.versions.append(current_version)
                self.logger.debug(f"Сохранена версия документа с ID: {id}, version_id: {current_version.version_id}")
            except Exception as e:
                self.logger.error(f"Ошибка при создании версии документа с ID: {id}: {str(e)}")
                raise

            # Применяем обновления
            if data.title is not None:
                mongo_doc.title = data.title
            if data.content is not None:
                mongo_doc.content = data.content
            if data.status is not None:
                mongo_doc.status = data.status
            if data.metadata is not None:
                mongo_doc.metadata = data.metadata
            if data.comments is not None:
                mongo_doc.comments = data.comments
            mongo_doc.updated_at = datetime.utcnow()

            # Сохраняем обновленный документ
            try:
                await mongo_doc.save()
                self.logger.debug(f"Документ с ID: {id} успешно обновлен")
                return self.mapper.to_domain_document(mongo_doc)
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении документа с ID: {id}: {str(e)}")
                raise
        self.logger.warning(f"Документ с ID: {id} не найден или помечен как удаленный")
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def delete(self, id: UUID) -> bool:
        """
        Выполняет мягкое удаление документа в MongoDB.

        Args:
            id: UUID документа.

        Returns:
            bool: True, если документ успешно помечен как удаленный, иначе False.
        """
        self.logger.debug(f"Мягкое удаление документа из MongoDB с ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
        if mongo_doc:
            mongo_doc.is_deleted = True
            mongo_doc.updated_at = datetime.utcnow()
            await mongo_doc.save()
            return True
        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        """
        Получает список документов из MongoDB с пагинацией.

        Args:
            skip: Количество документов для пропуска.
            limit: Максимальное количество документов для возврата.

        Returns:
            List[Document]: Список доменных моделей документов.
        """
        self.logger.debug(f"Получение документов из MongoDB с skip: {skip}, limit: {limit}")
        mongo_docs = await MongoDocument.find(MongoDocument.is_deleted == False).skip(skip).limit(limit).to_list()
        return [self.mapper.to_domain_document(doc) for doc in mongo_docs]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: retry_state.outcome.exception() and retry_state.outcome.exception().args[0]
    )
    async def restore(self, id: UUID) -> Optional[Document]:
        """
        Восстанавливает удаленный документ в MongoDB.

        Args:
            id: UUID документа.

        Returns:
            Document: Восстановленная доменная модель документа, если найдена.
            None: Если документ не найден.
        """
        self.logger.debug(f"Восстановление документа в MongoDB с ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == True)
        if mongo_doc:
            mongo_doc.is_deleted = False
            mongo_doc.updated_at = datetime.utcnow()
            await mongo_doc.save()
            return self.mapper.to_domain_document(mongo_doc)
        return None