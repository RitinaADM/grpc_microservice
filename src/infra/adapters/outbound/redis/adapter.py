import json
from typing import List, Optional
from redis.asyncio import Redis
from redis.exceptions import RedisError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.domain.models.document import Document, DocumentVersion
from src.infra.adapters.outbound.redis.mapper import RedisMapper
from src.infra.config.settings import settings
import logging
from src.domain.exceptions.base import BaseAppException

class RedisCacheAdapter:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.mapper = RedisMapper()
        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Получает документ из кэша по ID."""
        self.logger.debug(f"Getting document from cache: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document:{document_id}")
            return self.mapper.from_storage(cached_data) if cached_data else None
        except RedisError as e:
            self.logger.error(f"Error fetching document from cache: {str(e)}")
            raise BaseAppException(f"Failed to fetch document from cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document(self, document: Document) -> None:
        """Сохраняет документ в кэш."""
        self.logger.debug(f"Setting document in cache: {document.id}")
        try:
            serialized_data = self.mapper.to_storage(document)
            await self.redis_client.setex(f"document:{document.id}", settings.CACHE_TTL, serialized_data)
            self.logger.debug(f"Document cached: {document.id}")
        except RedisError as e:
            self.logger.error(f"Error setting document cache: {str(e)}")
            raise BaseAppException(f"Failed to set document cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def get_document_list(self, skip: int, limit: int) -> Optional[List[Document]]:
        """Получает список документов из кэша."""
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Getting document list from cache: {cache_key}")
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self.logger.debug(f"Cache hit for document list: {cache_key}")
                doc_list = json.loads(cached_data)
                return [self.mapper.from_storage(doc_data) for doc_data in doc_list]
            return None
        except RedisError as e:
            self.logger.error(f"Error getting document list from cache: {str(e)}")
            raise BaseAppException(f"Failed to get document list from cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document_list(self, documents: List[Document], skip: int, limit: int) -> None:
        """Сохраняет список документов в кэш."""
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Setting document list to cache: {cache_key}")
        try:
            serialized_list = [self.mapper.to_storage(doc) for doc in documents]
            await self.redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(serialized_list))
            self.logger.debug(f"Document list cached successfully: {cache_key}")
        except RedisError as e:
            self.logger.error(f"Error setting document list to cache: {str(e)}")
            raise BaseAppException(f"Failed to set document list cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document(self, document_id: str) -> None:
        """Инвалидирует кэш документа."""
        self.logger.debug(f"Invalidating document: {document_id}")
        try:
            await self.redis_client.delete(f"document:{document_id}")
            self.logger.debug(f"Document invalidated: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error invalidating document cache: {str(e)}")
            raise BaseAppException(f"Failed to invalidate document cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def get_document_versions(self, document_id: str) -> Optional[List[DocumentVersion]]:
        """Получает версии документа из кэша."""
        self.logger.debug(f"Fetching versions for document: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document_versions:{document_id}")
            return self.mapper.from_storage_versions(cached_data) if cached_data else None
        except RedisError as e:
            self.logger.error(f"Error fetching document versions from cache: {str(e)}")
            raise BaseAppException(f"Failed to fetch document versions from cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document_versions(self, document_id: str, versions: List[DocumentVersion]) -> None:
        """Сохраняет версии документа в кэш."""
        self.logger.debug(f"Setting document versions to cache: {document_id}")
        try:
            serialized_data = self.mapper.to_storage_versions(versions)
            await self.redis_client.setex(f"document_versions:{document_id}", settings.CACHE_TTL, serialized_data)
            self.logger.debug(f"Document versions cached: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error setting document versions cache: {str(e)}")
            raise BaseAppException(f"Failed to set document versions cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document_versions(self, document_id: str) -> None:
        """Инвалидирует кэш версий документа."""
        self.logger.debug(f"Invalidating document versions: {document_id}")
        try:
            await self.redis_client.delete(f"document_versions:{document_id}")
            self.logger.debug(f"Document versions invalidated: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error invalidating document versions cache: {str(e)}")
            raise BaseAppException(f"Failed to invalidate document versions cache: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document_list(self) -> None:
        """Инвалидирует кэш списков документов."""
        self.logger.debug("Invalidating document list cache")
        try:
            keys = await self.redis_client.keys("documents:skip=*:limit=*")
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.debug(f"Invalidated {len(keys)} document list cache entries")
        except RedisError as e:
            self.logger.error(f"Error invalidating document list cache: {str(e)}")
            raise BaseAppException(f"Failed to invalidate document list cache: {str(e)}")

    async def close(self) -> None:
        """Зак四大ствует соединение с Redis."""
        self.logger.debug("Closing Redis connection")
        try:
            await self.redis_client.aclose()
            self.logger.debug("Redis connection closed successfully")
        except RedisError as e:
            self.logger.error(f"Failed to close Redis connection: {str(e)}")
            raise BaseAppException(f"Failed to close Redis connection: {str(e)}")