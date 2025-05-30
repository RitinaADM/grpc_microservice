from beanie import Document as BeanieDocument
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from src.domain.models.document import DocumentStatus, DocumentMetadata, DocumentVersion

class MongoDocument(BeanieDocument):
    id: UUID
    title: str
    content: str
    status: DocumentStatus
    metadata: DocumentMetadata
    comments: List[str]
    versions: List[DocumentVersion]  # Добавляем версии
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Settings:
        name = "documents"