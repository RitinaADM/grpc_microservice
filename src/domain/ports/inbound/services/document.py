from abc import ABC, abstractmethod
from uuid import UUID
from src.domain.models.document import Document

class DocumentServicePort(ABC):
    """Inbound порт для взаимодействия внешнего мира с приложением."""
    @abstractmethod
    async def get_by_id(self, id: str) -> Document:
        pass

    @abstractmethod
    async def create(self, data: dict) -> Document:
        pass

    @abstractmethod
    async def update(self, id: str, data: dict) -> Document:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass