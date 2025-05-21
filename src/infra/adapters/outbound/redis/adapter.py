import json
from typing import Optional, List
from redis.asyncio import Redis
from src.domain.models.document import Document
import logging
from logging import Logger
from src.infra.config.settings import settings
from uuid import UUID
from datetime import datetime

class RedisCacheAdapter:
    """Адаптер для работы с Redis в качестве кэша."""

    def __init__(self, redis_client: Redis):
        """Инициализация адаптера с клиентом Redis."""
        self.redis: Redis = redis_client
        self.logger: Logger = logging.getLogger(__name__)

    def _serialize_document(self, document: Document) -> dict:
        """Сериализация документа в JSON-совместимый словарь."""
        doc_dict = document.dict()
        doc_dict['id'] = str(doc_dict['id'])  # Преобразуем UUID в строку
        doc_dict['created_at'] = doc_dict['created_at'].isoformat()  # Преобразуем datetime в строку
        doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()  # Преобразуем datetime в строку
        return doc_dict

    def _deserialize_document(self, doc_dict: dict) -> Document:
        """Десериализация словаря в объект Document."""
        doc_dict['id'] = UUID(doc_dict['id'])  # Преобразуем строку в UUID
        doc_dict['created_at'] = datetime.fromisoformat(doc_dict['created_at'])  # Преобразуем строку в datetime
        doc_dict['updated_at'] = datetime.fromisoformat(doc_dict['updated_at'])  # Преобразуем строку в datetime
        return Document(**doc_dict)

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Получение документа из кэша по ID."""
        self.logger.debug(f"Fetching document from cache: {document_id}")
        try:
            cached = await self.redis.get(f"document:{document_id}")
            if cached:
                self.logger.debug(f"Cache hit for document: {document_id}")
                document_dict = json.loads(cached)
                return self._deserialize_document(document_dict)
            self.logger.debug(f"Cache miss for document: {document_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching document from cache: {str(e)}")
            return None

    async def set_document(self, document: Document) -> None:
        """Сохранение документа в кэш."""
        self.logger.debug(f"Setting document in cache: {document.id}")
        try:
            document_dict = self._serialize_document(document)
            await self.redis.setex(
                f"document:{document.id}",
                settings.CACHE_TTL,
                json.dumps(document_dict)
            )
            self.logger.debug(f"Document cached: {document.id}")
        except Exception as e:
            self.logger.error(f"Error setting document in cache: {str(e)}")

    async def get_document_list(self, skip: int, limit: int) -> Optional[List[Document]]:
        """Получение списка документов из кэша."""
        cache_key = f"documents:skip:{skip}:limit:{limit}"
        self.logger.debug(f"Fetching document list from cache: {cache_key}")
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for document list: {cache_key}")
                documents_dict = json.loads(cached)
                return [self._deserialize_document(doc_dict) for doc_dict in documents_dict]
            self.logger.debug(f"Cache miss for document list: {cache_key}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching document list from cache: {str(e)}")
            return None

    async def set_document_list(self, documents: List[Document], skip: int, limit: int) -> None:
        """Сохранение списка документов в кэш."""
        cache_key = f"documents:skip:{skip}:limit:{limit}"
        self.logger.debug(f"Setting document list in cache: {cache_key}")
        try:
            documents_dict = [self._serialize_document(doc) for doc in documents]
            await self.redis.setex(
                cache_key,
                settings.CACHE_TTL,
                json.dumps(documents_dict)
            )
            self.logger.debug(f"Document list cached: {cache_key}")
        except Exception as e:
            self.logger.error(f"Error setting document list in cache: {str(e)}")

    async def invalidate_document(self, document_id: str) -> None:
        """Инвалидация кэша для конкретного документа."""
        self.logger.debug(f"Invalidating cache for document: {document_id}")
        try:
            await self.redis.delete(f"document:{document_id}")
            self.logger.debug(f"Cache invalidated for document: {document_id}")
        except Exception as e:
            self.logger.error(f"Error invalidating document cache: {str(e)}")

    async def invalidate_document_list(self) -> None:
        """Инвалидация кэша для всех списков документов."""
        self.logger.debug("Invalidating cache for all document lists")
        try:
            keys = await self.redis.keys("documents:skip:*")
            if keys:
                await self.redis.delete(*keys)
                self.logger.debug(f"Invalidated {len(keys)} document list cache entries")
        except Exception as e:
            self.logger.error(f"Error invalidating document list cache: {str(e)}")

    async def close(self) -> None:
        """Закрытие соединения с Redis."""
        self.logger.debug("Closing Redis connection")
        try:
            await self.redis.aclose()
            self.logger.debug("Redis connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {str(e)}")