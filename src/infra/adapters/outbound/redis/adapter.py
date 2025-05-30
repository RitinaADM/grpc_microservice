import json
from typing import List, Optional
from redis.asyncio import Redis
from redis.exceptions import RedisError
from src.domain.models.document import Document, DocumentStatus, DocumentVersion
from datetime import datetime
from uuid import UUID
import logging
from src.infra.config.settings import settings

class RedisCacheAdapter:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def _serialize_document(self, document: Document) -> str:
        doc_dict = document.dict()
        doc_dict['id'] = str(doc_dict['id'])
        doc_dict['created_at'] = doc_dict['created_at'].isoformat()
        doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()
        doc_dict['status'] = doc_dict['status'].value
        for version in doc_dict['versions']:
            version['version_id'] = str(version['version_id'])
            version['timestamp'] = version['timestamp'].isoformat()
            version['document']['id'] = str(version['document']['id'])
            version['document']['created_at'] = version['document']['created_at'].isoformat()
            version['document']['updated_at'] = version['document']['updated_at'].isoformat()
            version['document']['status'] = version['document']['status'].value
        return json.dumps(doc_dict)

    def _deserialize_document(self, data: str) -> Document:
        doc_dict = json.loads(data)
        doc_dict['id'] = UUID(doc_dict['id'])
        doc_dict['created_at'] = datetime.fromisoformat(doc_dict['created_at'])
        doc_dict['updated_at'] = datetime.fromisoformat(doc_dict['updated_at'])
        doc_dict['status'] = DocumentStatus(doc_dict['status'])
        for version in doc_dict['versions']:
            version['version_id'] = UUID(version['version_id'])
            version['timestamp'] = datetime.fromisoformat(version['timestamp'])
            version['document']['id'] = UUID(version['document']['id'])
            version['document']['created_at'] = datetime.fromisoformat(version['document']['created_at'])
            version['document']['updated_at'] = datetime.fromisoformat(version['document']['updated_at'])
            version['document']['status'] = DocumentStatus(version['document']['status'])
        return Document(**doc_dict)

    async def get_document(self, document_id: str) -> Optional[Document]:
        self.logger.debug(f"Getting document from cache: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document:{document_id}")
            if cached_data:
                self.logger.debug(f"Cache hit for document: {document_id}")
                return self._deserialize_document(cached_data)
            return None
        except RedisError as e:
            self.logger.error(f"Error fetching document from cache: {str(e)}")
            return None

    async def set_document(self, document: Document) -> None:
        self.logger.debug(f"Setting document in cache: {document.id}")
        try:
            serialized_data = self._serialize_document(document)
            await self.redis_client.setex(f"document:{document.id}", settings.CACHE_TTL, serialized_data)
            self.logger.debug(f"Document cached: {document.id}")
        except RedisError as e:
            self.logger.error(f"Error setting document cache: {str(e)}")

    async def get_document_list(self, skip: int, limit: int) -> Optional[List[Document]]:
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Getting document list from cache: {cache_key}")
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self.logger.debug(f"Cache hit for document list: {cache_key}")
                doc_list = json.loads(cached_data)
                return [self._deserialize_document(doc_data) for doc_data in doc_list]
            return None
        except RedisError as e:
            self.logger.error(f"Error getting document list from cache: {str(e)}")
            return None

    async def set_document_list(self, documents: List[Document], skip: int, limit: int) -> None:
        cache_key = f"documents:skip={skip}:limit={limit}"
        self.logger.debug(f"Setting document list to cache: {cache_key}")
        try:
            serialized_list = [self._serialize_document(doc) for doc in documents]
            await self.redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(serialized_list))
            self.logger.debug(f"Document list cached successfully: {cache_key}")
        except RedisError as e:
            self.logger.error(f"Error setting document list to cache: {str(e)}")

    async def invalidate_document(self, document_id: str) -> None:
        self.logger.debug(f"Invalidating document: {document_id}")
        try:
            await self.redis_client.delete(f"document:{document_id}")
            self.logger.debug(f"Document invalidated: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error invalidating document cache: {str(e)}")

    async def get_document_versions(self, document_id: str) -> Optional[List[DocumentVersion]]:
        self.logger.debug(f"Fetching versions for document: {document_id}")
        try:
            cached_data = await self.redis_client.get(f"document_versions:{document_id}")
            if cached_data:
                self.logger.debug(f"Cache hit for document versions: {document_id}")
                versions_data = json.loads(cached_data)
                versions = []
                for v_data in versions_data:
                    v_data['version_id'] = UUID(v_data['version_id'])
                    v_data['timestamp'] = datetime.fromisoformat(v_data['timestamp'])
                    v_data['document']['id'] = UUID(v_data['document']['id'])
                    v_data['document']['created_at'] = datetime.fromisoformat(v_data['document']['created_at'])
                    v_data['document']['updated_at'] = datetime.fromisoformat(v_data['document']['updated_at'])
                    v_data['document']['status'] = DocumentStatus(v_data['document']['status'])
                    versions.append(DocumentVersion(**v_data))
                return versions
            return None
        except RedisError as e:
            self.logger.error(f"Error fetching document versions from cache: {str(e)}")
            return None

    async def set_document_versions(self, document_id: str, versions: List[DocumentVersion]) -> None:
        self.logger.debug(f"Setting document versions to cache: {document_id}")
        try:
            versions_data = []
            for version in versions:
                version_data = version.dict()
                version_data['version_id'] = str(version_data['version_id'])
                version_data['timestamp'] = version_data['timestamp'].isoformat()
                version_data['document']['id'] = str(version_data['document']['id'])
                version_data['document']['created_at'] = version_data['document']['created_at'].isoformat()
                version_data['document']['updated_at'] = version_data['document']['updated_at'].isoformat()
                version_data['document']['status'] = version_data['document']['status'].value
                versions_data.append(version_data)
            await self.redis_client.setex(f"document_versions:{document_id}", settings.CACHE_TTL, json.dumps(versions_data))
            self.logger.debug(f"Document versions cached: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error setting document versions cache: {str(e)}")

    async def invalidate_document_versions(self, document_id: str) -> None:
        self.logger.debug(f"Invalidating document versions: {document_id}")
        try:
            await self.redis_client.delete(f"document_versions:{document_id}")
            self.logger.debug(f"Document versions invalidated: {document_id}")
        except RedisError as e:
            self.logger.error(f"Error invalidating document versions cache: {str(e)}")

    async def invalidate_document_list(self) -> None:
        self.logger.debug("Invalidating document list cache")
        try:
            keys = await self.redis_client.keys("documents:skip=*:limit=*")
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.debug(f"Invalidated {len(keys)} document list cache entries")
        except RedisError as e:
            self.logger.error(f"Error invalidating document list cache: {str(e)}")

    async def close(self) -> None:
        self.logger.debug("Closing Redis connection")
        try:
            await self.redis_client.aclose()
            self.logger.debug("Redis connection closed successfully")
        except RedisError as e:
            self.logger.error(f"Failed to close Redis connection: {str(e)}")
            raise