from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.models.document import Document, DocumentVersion
from src.application.document.dto import DocumentUpdateDTO

class DocumentRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[Document]:
        pass

    @abstractmethod
    async def save(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

    @abstractmethod
    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        pass

    @abstractmethod
    async def restore(self, id: UUID) -> Optional[Document]:
        pass

    @abstractmethod
    async def get_versions(self, id: UUID) -> List[DocumentVersion]:
        pass