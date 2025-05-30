from beanie import Document as BeanieDocument
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from src.domain.models.document import DocumentStatus, DocumentVersion

class MongoDocument(BeanieDocument):
    id: UUID
    title: str
    content: str
    status: DocumentStatus
    author: str
    tags: List[str]
    category: Optional[str]
    comments: List[str]
    versions: List[DocumentVersion]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Settings:
        name = "documents"