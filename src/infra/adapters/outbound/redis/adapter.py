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
        self.logger.debug(f"Получение документа из кэша: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document:{document_id}")
            return self.mapper.from_storage(cached_data) if cached_data else None
        except RedisError as e:
            self.logger.error(f"Ошибка при получении документа из кэша: {str(e)}")
            raise BaseAppException(f"Не удалось получить документ из кэша: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document(self, document: Document) -> None:
        """Сохраняет документ в кэш."""
        self.logger.debug(f"Сохранение документа в кэш: {document.id}")
        try:
            serialized_data = self.mapper.to_storage(document)
            await self.redis_client.setex(f"document:{document.id}", settings.CACHE_TTL, serialized_data)
            self.logger.debug(f"Документ успешно закэширован: {document.id}")
        except RedisError as e:
            self.logger.error(f"Ошибка при сохранении документа в кэш: {str(e)}")
            raise BaseAppException(f"Не удалось сохранить документ в кэш: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def get_document_list(self, skip: int, limit: int) -> Optional[List[Document]]:
        """Получает список документов из кэша."""
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Получение списка документов из кэша: {cache_key}")
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self.logger.debug(f"Кэш-попадание для списка документов: {cache_key}")
                doc_list = json.loads(cached_data)
                return [self.mapper.from_storage(doc_data) for doc_data in doc_list]
            return None
        except RedisError as e:
            self.logger.error(f"Ошибка при получении списка документов из кэша: {str(e)}")
            raise BaseAppException(f"Не удалось получить список документов из кэша: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document_list(self, documents: List[Document], skip: int, limit: int) -> None:
        """Сохраняет список документов в кэш."""
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Сохранение списка документов в кэш: {cache_key}")
        try:
            serialized_list = [self.mapper.to_storage(doc) for doc in documents]
            await self.redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(serialized_list))
            self.logger.debug(f"Список документов успешно закэширован: {cache_key}")
        except RedisError as e:
            self.logger.error(f"Ошибка при сохранении списка документов в кэш: {str(e)}")
            raise BaseAppException(f"Не удалось сохранить список документов в кэш: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document(self, document_id: str) -> None:
        """Инвалидирует кэш документа."""
        self.logger.debug(f"Инвалидация документа: {document_id}")
        try:
            await self.redis_client.delete(f"document:{document_id}")
            self.logger.debug(f"Документ успешно инвалидирован: {document_id}")
        except RedisError as e:
            self.logger.error(f"Ошибка при инвалидации кэша документа: {str(e)}")
            raise BaseAppException(f"Не удалось инвалидировать кэш документа: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def get_document_versions(self, document_id: str) -> Optional[List[DocumentVersion]]:
        """Получает версии документа из кэша."""
        self.logger.debug(f"Получение версий документа: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document_versions:{document_id}")
            return self.mapper.from_storage_versions(cached_data) if cached_data else None
        except RedisError as e:
            self.logger.error(f"Ошибка при получении версий документа из кэша: {str(e)}")
            raise BaseAppException(f"Не удалось получить версии документа из кэша: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def set_document_versions(self, document_id: str, versions: List[DocumentVersion]) -> None:
        """Сохраняет версии документа в кэш."""
        self.logger.debug(f"Сохранение версий документа в кэш: {document_id}")
        try:
            serialized_data = self.mapper.to_storage_versions(versions)
            await self.redis_client.setex(f"document_versions:{document_id}", settings.CACHE_TTL, serialized_data)
            self.logger.debug(f"Версии документа успешно закэшированы: {document_id}")
        except RedisError as e:
            self.logger.error(f"Ошибка при сохранении версий документа в кэш: {str(e)}")
            raise BaseAppException(f"Не удалось сохранить версии документа в кэш: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document_versions(self, document_id: str) -> None:
        """Инвалидирует кэш версий документа."""
        self.logger.debug(f"Инвалидация версий документа: {document_id}")
        try:
            await self.redis_client.delete(f"document_versions:{document_id}")
            self.logger.debug(f"Версии документа успешно инвалидированы: {document_id}")
        except RedisError as e:
            self.logger.error(f"Ошибка при инвалидации кэша версий документа: {str(e)}")
            raise BaseAppException(f"Не удалось инвалидировать кэш версий документа: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RedisError)
    )
    async def invalidate_document_list(self) -> None:
        """Инвалидирует кэш списков документов."""
        self.logger.debug("Инвалидация кэша списка документов")
        try:
            keys = await self.redis_client.keys("documents:skip=*:limit=*")
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.debug(f"Инвалидировано {len(keys)} записей кэша списка документов")
        except RedisError as e:
            self.logger.error(f"Ошибка при инвалидации кэша списка документов: {str(e)}")
            raise BaseAppException(f"Не удалось инвалидировать кэш списка документов: {str(e)}")

    async def close(self) -> None:
        """Закрывает соединение с Redis."""
        self.logger.debug("Закрытие соединения с Redis")
        try:
            await self.redis_client.aclose()
            self.logger.debug("Соединение с Redis успешно закрыто")
        except RedisError as e:
            self.logger.error(f"Не удалось закрыть соединение с Redis: {str(e)}")
            raise BaseAppException(f"Не удалось закрыть соединение с Redis: {str(e)}")