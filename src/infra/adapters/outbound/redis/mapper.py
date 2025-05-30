import json
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion, DocumentStatus
from src.domain.ports.outbound.mappers.base import BaseMapper

class RedisMapper(BaseMapper[Document]):
    """Маппер для сериализации/десериализации данных в Redis."""

    def _convert_to_json_serializable(self, obj: Any) -> Any:
        """Рекурсивно преобразует UUID и datetime в JSON-сериализуемые типы."""
        if isinstance(obj, UUID):
            return self._serialize_uuid(obj)
        if isinstance(obj, datetime):
            return self._serialize_datetime(obj)
        if isinstance(obj, DocumentStatus):
            return self._serialize_status(obj)
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        return obj

    def to_storage(self, obj: Document) -> str:
        """Сериализует Document в JSON-строку для Redis."""
        doc_dict = obj.dict()
        doc_dict = self._convert_to_json_serializable(doc_dict)
        return json.dumps(doc_dict)

    def from_storage(self, data: str) -> Document:
        """Десериализует JSON-строку из Redis в Document."""
        doc_dict = json.loads(data)
        doc_dict['id'] = self._deserialize_uuid(doc_dict['id'])
        doc_dict['created_at'] = self._deserialize_datetime(doc_dict['created_at'])
        doc_dict['updated_at'] = self._deserialize_datetime(doc_dict['updated_at'])
        doc_dict['status'] = self._deserialize_status(doc_dict['status'])
        for version in doc_dict['versions']:
            version['version_id'] = self._deserialize_uuid(version['version_id'])
            version['timestamp'] = self._deserialize_datetime(version['timestamp'])
            version['document']['id'] = self._deserialize_uuid(version['document']['id'])
            version['document']['created_at'] = self._deserialize_datetime(version['document']['created_at'])
            version['document']['updated_at'] = self._deserialize_datetime(version['document']['updated_at'])
            version['document']['status'] = self._deserialize_status(version['document']['status'])
        return Document(**doc_dict)

    def to_storage_versions(self, versions: List[DocumentVersion]) -> str:
        """Сериализует список DocumentVersion в JSON-строку для Redis."""
        versions_data = [version.dict() for version in versions]
        versions_data = self._convert_to_json_serializable(versions_data)
        return json.dumps(versions_data)

    def from_storage_versions(self, data: str) -> List[DocumentVersion]:
        """Десериализует JSON-строку из Redis в список DocumentVersion."""
        versions_data = json.loads(data)
        versions = []
        for v_data in versions_data:
            v_data['version_id'] = self._deserialize_uuid(v_data['version_id'])
            v_data['timestamp'] = self._deserialize_datetime(v_data['timestamp'])
            v_data['document']['id'] = self._deserialize_uuid(v_data['document']['id'])
            v_data['document']['created_at'] = self._deserialize_datetime(v_data['document']['created_at'])
            v_data['document']['updated_at'] = self._deserialize_datetime(v_data['document']['updated_at'])
            v_data['document']['status'] = self._deserialize_status(v_data['document']['status'])
            versions.append(DocumentVersion(**v_data))
        return versions