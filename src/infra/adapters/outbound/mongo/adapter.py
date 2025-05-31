import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pymongo.errors import ConnectionFailure, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.domain.models.document import Document, DocumentVersion
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.application.document.dto import DocumentUpdateDTO
from src.infra.adapters.outbound.mongo.mapper import MongoMapper
from src.domain.exceptions.base import BaseAppException

class MongoDocumentAdapter(DocumentRepositoryPort):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mapper = MongoMapper()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def get_by_id(self, id: UUID) -> Optional[Document]:
        self.logger.debug(f"Получение документа из MongoDB с ID: {id}")
        try:
            mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
            return self.mapper.to_domain_document(mongo_doc) if mongo_doc else None
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при получении документа {id}: {str(e)}")
            raise BaseAppException(f"Не удалось получить документ из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def save(self, document: Document) -> Document:
        self.logger.debug(f"Создание документа в MongoDB: {document.id}")
        try:
            mongo_doc = self.mapper.to_mongo_document(document)
            await mongo_doc.save()
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при создании документа {document.id}: {str(e)}")
            raise BaseAppException(f"Не удалось создать документ из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        self.logger.debug(f"Обновление документа в MongoDB с ID: {id}")
        try:
            mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
            if not mongo_doc:
                self.logger.warning(f"Документ с ID: {id} не найден или удален")
                return None
            current_version = DocumentVersion(
                version_id=uuid4(),
                document=self.mapper.to_domain_document(mongo_doc),
                timestamp=datetime.utcnow()
            )
            mongo_doc.versions.append(current_version)
            if data.title is not None:
                mongo_doc.title = data.title
            if data.content is not None:
                mongo_doc.content = data.content
            if data.status is not None:
                mongo_doc.status = data.status
            if data.author is not None:
                mongo_doc.author = data.author
            if data.tags is not None:
                mongo_doc.tags = data.tags
            if data.category is not None:
                mongo_doc.category = data.category
            if data.comments is not None:
                mongo_doc.comments = data.comments
            mongo_doc.updated_at = datetime.utcnow()
            await mongo_doc.save()
            return self.mapper.to_domain_document(mongo_doc)
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при обновлении документа {id}: {str(e)}")
            raise BaseAppException(f"Не удалось обновить документ из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def delete(self, id: UUID) -> bool:
        self.logger.debug(f"Мягкое удаление документа из MongoDB с ID: {id}")
        try:
            mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == False)
            if mongo_doc:
                mongo_doc.is_deleted = True
                mongo_doc.updated_at = datetime.utcnow()
                await mongo_doc.save()
                return True
            return False
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при удалении документа {id}: {str(e)}")
            raise BaseAppException(f"Не удалось удалить документ;"
                                  f" из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        self.logger.debug(f"Получение списка документов из MongoDB с пропуском: {skip}, лимитом: {limit}")
        try:
            mongo_docs = await MongoDocument.find(MongoDocument.is_deleted == False).skip(skip).limit(limit).to_list()
            return [self.mapper.to_domain_document(doc) for doc in mongo_docs]
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при получении списка документов: {str(e)}")
            raise BaseAppException(f"Не удалось получить список документов из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def restore(self, id: UUID) -> Optional[Document]:
        self.logger.debug(f"Восстановление документа в MongoDB с ID: {id}")
        try:
            mongo_doc = await MongoDocument.find_one(MongoDocument.id == id, MongoDocument.is_deleted == True)
            if mongo_doc:
                mongo_doc.is_deleted = False
                mongo_doc.updated_at = datetime.utcnow()
                await mongo_doc.save()
                return self.mapper.to_domain_document(mongo_doc)
            return None
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при восстановлении документа {id}: {str(e)}")
            raise BaseAppException(f"Не удалось восстановить документ из-за ошибки базы данных: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure))
    )
    async def get_versions(self, id: UUID) -> List[DocumentVersion]:
        self.logger.debug(f"Получение версий документа из MongoDB с ID: {id}")
        try:
            mongo_doc = await MongoDocument.find_one(MongoDocument.id == id)
            return mongo_doc.versions if mongo_doc else []
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Ошибка MongoDB при получении версий документа {id}: {str(e)}")
            raise BaseAppException(f"Не удалось получить версии документа из-за ошибки базы данных: {str(e)}")