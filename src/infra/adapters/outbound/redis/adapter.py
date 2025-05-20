import json
from typing import Optional, List
from redis.asyncio import Redis
from src.domain.models.document import Document
import logging
from logging import Logger
from src.infra.config.settings import settings

class RedisCacheAdapter:
    """Адаптер для работы с Redis в качестве кэша."""

    def __init__(self, redis_client: Redis):
        """Инициализация адаптера с клиентом Redis."""
        self.redis: Redis = redis_client
        self.logger: Logger = logging.getLogger(__name__)

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Получение документа из кэша по ID."""
        self.logger.debug(f"Fetching document from cache: {document_id}")
        try:
            cached = await self.redis.get(f"document:{document_id}")
            if cached:
                self.logger.debug(f"Cache hit for document: {document_id}")
                return Document(**json.loads(cached))
            self.logger.debug(f"Cache miss for document: {document_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching document from cache: {str(e)}")
            return None

    async def set_document(self, document: Document) -> None:
        """Сохранение документа в кэш."""
        self.logger.debug(f"Setting document in cache: {document.id}")
        try:
            await self.redis.setex(
                f"document:{document.id}",
                settings.CACHE_TTL,
                json.dumps(document.dict())
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
                return [Document(**doc) for doc in json.loads(cached)]
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
            await self.redis.setex(
                cache_key,
                settings.CACHE_TTL,
                json.dumps([doc.dict() for doc in documents])
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