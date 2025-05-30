import json
from typing import List, Optional
from src.domain.models.document import Document, DocumentVersion
from src.domain.ports.outbound.mappers.base import BaseMapper
from src.infra.adapters.outbound.mappers.utils import MapperUtils, VersionMapper

class RedisMapper(BaseMapper[Document]):
    """Маппер для сериализации/десериализации данных в Redis."""

    def to_storage(self, obj: Document) -> str:
        """Сериализует Document в JSON-строку для Redis."""
        doc_dict = MapperUtils.to_json_serializable(obj)
        return json.dumps(doc_dict)

    def from_storage(self, data: str) -> Document:
        """Десериализует JSON-строку из Redis в Document."""
        doc_dict = json.loads(data)
        doc_dict['id'] = MapperUtils.deserialize_uuid(doc_dict['id'])
        doc_dict['created_at'] = MapperUtils.deserialize_datetime(doc_dict['created_at'])
        doc_dict['updated_at'] = MapperUtils.deserialize_datetime(doc_dict['updated_at'])
        doc_dict['status'] = MapperUtils.deserialize_status(doc_dict['status'])
        doc_dict['tags'] = doc_dict.get('tags', [])
        doc_dict['comments'] = doc_dict.get('comments', [])
        doc_dict['versions'] = [VersionMapper.to_domain_version(v, "redis") for v in doc_dict.get('versions', [])]
        return Document(**doc_dict)

    def to_storage_versions(self, versions: List[DocumentVersion]) -> str:
        """Сериализует список DocumentVersion в JSON-строку для Redis."""
        return json.dumps(VersionMapper.to_storage_versions(versions, "redis"))

    def from_storage_versions(self, data: str) -> List[DocumentVersion]:
        """Десериализует JSON-строку из Redis в список DocumentVersion."""
        versions_data = json.loads(data)
        return [VersionMapper.to_domain_version(v, "redis") for v in versions_data]