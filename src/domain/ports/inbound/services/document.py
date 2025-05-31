from abc import ABC, abstractmethod
from src.domain.models.document import Document, DocumentVersion
from src.application.document.dto import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from typing import List
from uuid import UUID

class DocumentServicePort(ABC):
    """Inbound порт для взаимодействия внешнего мира с приложением."""
    @abstractmethod
    async def get_by_id(self, id_dto: DocumentIdDTO) -> Document:
        pass

    @abstractmethod
    async def create(self, data: DocumentCreateDTO) -> Document:
        pass

    @abstractmethod
    async def update(self, id_dto: DocumentIdDTO, data: DocumentUpdateDTO) -> Document:
        pass

    @abstractmethod
    async def delete(self, id_dto: DocumentIdDTO) -> bool:
        pass

    @abstractmethod
    async def list_documents(self, params: DocumentListDTO) -> List[Document]:
        pass

    @abstractmethod
    async def restore(self, id_dto: DocumentIdDTO) -> Document:
        """Восстановление документа по ID."""
        pass

    @abstractmethod
    async def get_versions(self, id_dto: DocumentIdDTO) -> List[DocumentVersion]:
        """Получение списка версий документа."""
        pass

    @abstractmethod
    async def get_version(self, id_dto: DocumentIdDTO, version_id: UUID) -> DocumentVersion:
        """Получение конкретной версии документа."""
        pass