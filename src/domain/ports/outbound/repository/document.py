from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.dtos.document import DocumentUpdateDTO
from src.domain.models.document import Document

class DocumentRepositoryPort(ABC):
    """Outbound порт для взаимодействия приложения с хранилищем данных."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Document]:
        """Получение документа по ID. Возвращает None, если документ не найден."""
        pass

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Создание нового документа."""
        pass

    @abstractmethod
    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        """Обновление документа по ID. Возвращает None, если документ не найден."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Мягкое удаление документа по ID. Возвращает True при успехе."""
        pass

    @abstractmethod
    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        """Получение списка документов с пагинацией."""
        pass

    @abstractmethod
    async def restore(self, id: UUID) -> Optional[Document]:
        """Восстановление удаленного документа по ID. Возвращает None, если документ не найден."""
        pass