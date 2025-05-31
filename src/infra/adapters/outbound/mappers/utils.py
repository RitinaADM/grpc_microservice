from typing import Any, List
from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion, DocumentStatus

class MapperUtils:
    """Утилитные методы для сериализации/десериализации данных в мапперах."""

    @staticmethod
    def serialize_uuid(value: UUID) -> str:
        """Сериализует UUID в строку."""
        return str(value)

    @staticmethod
    def deserialize_uuid(value: Any) -> UUID:
        """Десериализует строку или UUID в UUID."""
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            return UUID(value)
        raise ValueError(f"Неверное значение UUID: {value}")

    @staticmethod
    def serialize_datetime(value: datetime) -> str:
        """Сериализует datetime в строку ISO."""
        return value.isoformat()

    @staticmethod
    def deserialize_datetime(value: Any) -> datetime:
        """Десериализует строку ISO или datetime в datetime."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise ValueError(f"Неверное значение datetime: {value}")

    @staticmethod
    def serialize_status(value: DocumentStatus) -> str:
        """Сериализует DocumentStatus в строку."""
        return value.value

    @staticmethod
    def deserialize_status(value: str) -> DocumentStatus:
        """Десериализует строку в DocumentStatus."""
        return DocumentStatus(value)

    @staticmethod
    def to_json_serializable(obj: Any) -> Any:
        """Рекурсивно преобразует объект в JSON-сериализуемый формат."""
        if isinstance(obj, UUID):
            return MapperUtils.serialize_uuid(obj)
        if isinstance(obj, datetime):
            return MapperUtils.serialize_datetime(obj)
        if isinstance(obj, DocumentStatus):
            return MapperUtils.serialize_status(obj)
        if isinstance(obj, dict):
            return {k: MapperUtils.to_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [MapperUtils.to_json_serializable(item) for item in obj]
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):  # Для Pydantic моделей
            return MapperUtils.to_json_serializable(obj.model_dump())
        return obj

class VersionMapper:
    """Утилиты для обработки версий документов."""

    @staticmethod
    def to_domain_version(version_data: Any, storage_type: str) -> DocumentVersion:
        """Преобразует данные версии в доменную DocumentVersion."""
        if storage_type == "redis":
            version_dict = version_data
        elif storage_type == "sql":
            version_dict = version_data.document_data
            version_dict['version_id'] = version_data.version_id
            version_dict['timestamp'] = version_data.timestamp
        elif storage_type == "mongo":
            version_dict = version_data
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {storage_type}")

        version_dict['version_id'] = MapperUtils.deserialize_uuid(version_dict['version_id'])
        version_dict['timestamp'] = MapperUtils.deserialize_datetime(version_dict['timestamp'])
        document_dict = version_dict['document'] if storage_type != "sql" else version_dict
        document_dict['id'] = MapperUtils.deserialize_uuid(document_dict['id'])
        document_dict['created_at'] = MapperUtils.deserialize_datetime(document_dict['created_at'])
        document_dict['updated_at'] = MapperUtils.deserialize_datetime(document_dict['updated_at'])
        document_dict['status'] = MapperUtils.deserialize_status(document_dict['status'])
        document_dict['tags'] = document_dict.get('tags', [])
        document_dict['comments'] = document_dict.get('comments', [])
        document_dict['versions'] = []
        version_dict['document'] = Document(**document_dict)
        return DocumentVersion(**version_dict)

    @staticmethod
    def to_storage_versions(versions: List[DocumentVersion], storage_type: str) -> Any:
        """Сериализует список версий для хранилища."""
        serialized = MapperUtils.to_json_serializable(versions)
        if storage_type == "sql":
            return [{"version_id": v["version_id"], "timestamp": v["timestamp"], "document_data": v["document"]} for v in serialized]
        return serialized