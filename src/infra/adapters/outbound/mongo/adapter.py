import logging  # Исправлен импорт logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logging import Logger
from src.domain.models.document import Document as DomainDocument
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.dtos.document import DocumentUpdateDTO

class MongoDocumentAdapter(DocumentRepositoryPort):
    """Адаптер для работы с MongoDB."""

    def __init__(self):
        """Инициализация адаптера с настройкой логгера."""
        self.logger: Logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def get_by_id(self, id: UUID) -> Optional[DomainDocument]:
        """Получение документа по ID из MongoDB."""
        self.logger.debug(f"Fetching document from MongoDB with ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
        return self._to_domain(mongo_doc) if mongo_doc else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def create(self, document: DomainDocument) -> DomainDocument:
        """Создание документа в MongoDB."""
        self.logger.debug(f"Creating document in MongoDB: {document.id}")
        mongo_doc = self._to_mongo(document)
        await mongo_doc.insert()
        return document

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[DomainDocument]:
        """Обновление документа в MongoDB."""
        self.logger.debug(f"Updating document in MongoDB with ID: {id}, data: {data.dict(exclude_none=True)}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
        if mongo_doc:
            update_data = data.dict(exclude_none=True)
            for key, value in update_data.items():
                setattr(mongo_doc, key, value)
            mongo_doc.updated_at = datetime.utcnow()
            await mongo_doc.save()
            return self._to_domain(mongo_doc)
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def delete(self, id: UUID) -> bool:
        """Мягкое удаление документа из MongoDB."""
        self.logger.debug(f"Soft deleting document from MongoDB with ID: {id}")
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
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def list_documents(self, skip: int, limit: int) -> List[DomainDocument]:
        """Получение списка документов из MongoDB с пагинацией."""
        self.logger.debug(f"Fetching documents from MongoDB with skip: {skip}, limit: {limit}")
        mongo_docs = await MongoDocument.find(MongoDocument.is_deleted == False).skip(skip).limit(limit).to_list()
        return [self._to_domain(doc) for doc in mongo_docs]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        before_sleep=lambda retry_state: logging.getLogger(__name__).warning(
            f"Retrying operation (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )
    async def restore(self, id: UUID) -> Optional[DomainDocument]:
        """Восстановление документа в MongoDB."""
        self.logger.debug(f"Restoring document in MongoDB with ID: {id}")
        mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == True)
        if mongo_doc:
            mongo_doc.is_deleted = False
            mongo_doc.updated_at = datetime.utcnow()
            await mongo_doc.save()
            return self._to_domain(mongo_doc)
        return None

    def _to_domain(self, mongo_doc: Optional[MongoDocument]) -> Optional[DomainDocument]:
        """Конвертация MongoDB документа в доменную модель."""
        if not mongo_doc:
            return None
        return DomainDocument(
            id=mongo_doc.id,
            title=mongo_doc.title,
            content=mongo_doc.content,
            created_at=mongo_doc.created_at,
            updated_at=mongo_doc.updated_at,
            is_deleted=mongo_doc.is_deleted
        )

    def _to_mongo(self, document: DomainDocument) -> MongoDocument:
        """Конвертация доменной модели в MongoDB документ."""
        return MongoDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_deleted=document.is_deleted
        )