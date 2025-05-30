import json
from typing import Optional, List
from redis.asyncio import Redis
from src.domain.models.document import Document, DocumentMetadata, DocumentStatus, DocumentVersion
import logging
from logging import Logger
from src.infra.config.settings import settings
from uuid import UUID
from datetime import datetime

class RedisCacheAdapter:
    def __init__(self, redis_client: Redis):
        self.redis: Redis = redis_client
        self.logger: Logger = logging.getLogger(__name__)

    def _serialize_document(self, document: Document) -> dict:
        doc_dict = document.dict()
        doc_dict['id'] = str(doc_dict['id'])
        doc_dict['created_at'] = doc_dict['created_at'].isoformat()
        doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()
        doc_dict['status'] = doc_dict['status'].value
        for version in doc_dict['versions']:
            version['version_id'] = str(version['version_id'])
            version['timestamp'] = version['timestamp'].isoformat()
        return doc_dict

    def _deserialize_document(self, doc_dict: dict) -> Document:
        doc_dict['id'] = UUID(doc_dict['id'])
        doc_dict['created_at'] = datetime.fromisoformat(doc_dict['created_at'])
        doc_dict['updated_at'] = datetime.fromisoformat(doc_dict['updated_at'])
        doc_dict['status'] = DocumentStatus(doc_dict['status'])
        doc_dict['metadata'] = DocumentMetadata(**doc_dict['metadata'])
        for version in doc_dict['versions']:
            version['version_id'] = UUID(version['version_id'])
            version['timestamp'] = datetime.fromisoformat(version['timestamp'])
            version['metadata'] = DocumentMetadata(**version['metadata'])
        return Document(**doc_dict)

    async def get_document(self, document_id: str) -> Optional[Document]:
        self.logger.debug(f"Получение документа из кэша: {document_id}")
        try:
            cached = await self.redis.get(f"document:{document_id}")
            if cached:
                self.logger.debug(f"Попадание в кэш для документа: {document_id}")
                document_dict = json.loads(cached)
                return self._deserialize_document(document_dict)
            self.logger.debug(f"Промах кэша для документа: {document_id}")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения документа из кэша: {str(e)}")
            return None

    async def set_document(self, document: Document) -> None:
        self.logger.debug(f"Установка документа в кэш: {document.id}")
        try:
            document_dict = self._serialize_document(document)
            await self.redis.setex(
                f"document:{document.id}",
                settings.CACHE_TTL,
                json.dumps(document_dict)
            )
            self.logger.debug(f"Документ закэширован: {document.id}")
        except Exception as e:
            self.logger.error(f"Ошибка установки документа в кэш: {str(e)}")

    async def get_document_list(self, skip: int, limit: int) -> Optional[List[Document]]:
        cache_key = f"documents:skip:{skip}:limit:{limit}"
        self.logger.debug(f"Получение списка документов из кэша: {cache_key}")
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                self.logger.debug(f"Попадание в кэш для списка документов: {cache_key}")
                documents_dict = json.loads(cached)
                return [self._deserialize_document(doc_dict) for doc_dict in documents_dict]
            self.logger.debug(f"Промах кэша для списка документов: {cache_key}")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения списка документов из кэша: {str(e)}")
            return None

    async def set_document_list(self, documents: List[Document], skip: int, limit: int) -> None:
        cache_key = f"documents:skip:{skip}:limit:{limit}"
        self.logger.debug(f"Установка списка документов в кэш: {cache_key}")
        try:
            documents_dict = [self._serialize_document(doc) for doc in documents]
            await self.redis.setex(
                cache_key,
                settings.CACHE_TTL,
                json.dumps(documents_dict)
            )
            self.logger.debug(f"Список документов закэширован: {cache_key}")
        except Exception as e:
            self.logger.error(f"Ошибка установки списка документов в кэш: {str(e)}")

    async def invalidate_document(self, document_id: str) -> None:
        self.logger.debug(f"Инвалидация кэша для документа: {document_id}")
        try:
            await self.redis.delete(f"document:{document_id}")
            self.logger.debug(f"Кэш инвалидирован для документа: {document_id}")
        except Exception as e:
            self.logger.error(f"Ошибка инвалидации кэша документа: {str(e)}")

    async def invalidate_document_list(self) -> None:
        self.logger.debug("Инвалидация кэша для всех списков документов")
        try:
            keys = await self.redis.keys("documents:skip:*")
            if keys:
                await self.redis.delete(*keys)
                self.logger.debug(f"Инвалидировано {len(keys)} записей кэша списков документов")
        except Exception as e:
            self.logger.error(f"Ошибка инвалидации кэша списков документов: {str(e)}")

    async def get_document_versions(self, document_id: str) -> Optional[List[DocumentVersion]]:
        """
        Получает список версий документа из кэша.

        Args:
            document_id: UUID документа в виде строки.

        Returns:
            List[DocumentVersion]: Список версий, если найдены в кэше.
            None: Если версии не найдены.
        """
        self.logger.debug(f"Получение версий документа из кэша: {document_id}")
        try:
            cached = await self.redis.get(f"document_versions:{document_id}")
            if cached:
                self.logger.debug(f"Попадание в кэш для версий документа: {document_id}")
                versions_dict = json.loads(cached)
                return [DocumentVersion(**{
                    'version_id': UUID(v['version_id']),
                    'content': v['content'],
                    'metadata': DocumentMetadata(**v['metadata']),
                    'comments': v['comments'],
                    'timestamp': datetime.fromisoformat(v['timestamp'])
                }) for v in versions_dict]
            self.logger.debug(f"Промах кэша для версий документа: {document_id}")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения версий из кэша: {str(e)}")
            return None

    async def set_document_versions(self, document_id: str, versions: List[DocumentVersion]) -> None:
        """
        Сохраняет список версий документа в кэш.

        Args:
            document_id: UUID документа в виде строки.
            versions: Список версий документа.
        """
        self.logger.debug(f"Установка версий документа в кэш: {document_id}")
        try:
            versions_dict = [{
                'version_id': str(v.version_id),
                'content': v.content,
                'metadata': v.metadata.dict(),
                'comments': v.comments,
                'timestamp': v.timestamp.isoformat()
            } for v in versions]
            await self.redis.setex(
                f"document_versions:{document_id}",
                settings.CACHE_TTL,
                json.dumps(versions_dict)
            )
            self.logger.debug(f"Версии документа закэшированы: {document_id}")
        except Exception as e:
            self.logger.error(f"Ошибка установки версий в кэш: {str(e)}")

    async def invalidate_document_versions(self, document_id: str) -> None:
        """
        Инвалидирует кэш версий документа.

        Args:
            document_id: UUID документа в виде строки.
        """
        self.logger.debug(f"Инвалидация кэша для версий документа: {document_id}")
        try:
            await self.redis.delete(f"document_versions:{document_id}")
            self.logger.debug(f"Кэш версий инвалидирован: {document_id}")
        except Exception as e:
            self.logger.error(f"Ошибка инвалидации кэша версий: {str(e)}")

    async def close(self) -> None:
        self.logger.debug("Закрытие соединения с Redis")
        try:
            await self.redis.aclose()
            self.logger.debug("Соединение с Redis закрыто")
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии соединения с Redis: {str(e)}")
            raise