from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

T = TypeVar('T')

class BaseMapper(ABC, Generic[T]):
    """Порт для мапперов, определяющий контракт сериализации/десериализации."""

    @abstractmethod
    def to_storage(self, obj: T) -> Any:
        """Сериализует доменный объект в формат хранилища."""
        pass

    @abstractmethod
    def from_storage(self, data: Any) -> T:
        """Десериализует данные из хранилища в доменный объект."""
        pass