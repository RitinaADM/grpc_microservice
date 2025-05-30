from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from uuid import UUID
from datetime import datetime
from src.domain.models.document import DocumentStatus

T = TypeVar('T')

class BaseMapper(ABC, Generic[T]):
    """Базовый класс для мапперов, обеспечивающий унифицированную сериализацию/десериализацию типов."""

    @staticmethod
    def _serialize_uuid(value: UUID) -> str:
        """Сериализует UUID в строку."""
        return str(value)

    @staticmethod
    def _deserialize_uuid(value: Any) -> UUID:
        """Десериализует строку или UUID в UUID."""
        if isinstance(value, UUID):
            return value  # Если уже UUID, возвращаем как есть
        if isinstance(value, str):
            return UUID(value)
        raise ValueError(f"Invalid UUID value: {value}")

    @staticmethod
    def _serialize_datetime(value: datetime) -> str:
        """Сериализует datetime в строку ISO."""
        return value.isoformat()

    @staticmethod
    def _deserialize_datetime(value: str) -> datetime:
        """Десериализует строку ISO в datetime."""
        return datetime.fromisoformat(value)

    @staticmethod
    def _serialize_status(value: DocumentStatus) -> str:
        """Сериализует DocumentStatus в строку."""
        return value.value

    @staticmethod
    def _deserialize_status(value: str) -> DocumentStatus:
        """Десериализует строку в DocumentStatus."""
        return DocumentStatus(value)

    @abstractmethod
    def to_storage(self, obj: T) -> Any:
        """Сериализует доменный объект в формат хранилища."""
        pass

    @abstractmethod
    def from_storage(self, data: Any) -> T:
        """Десериализует данные из хранилища в доменный объект."""
        pass