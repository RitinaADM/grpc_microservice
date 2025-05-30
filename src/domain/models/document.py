from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import List, Optional

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class DocumentMetadata(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None

class DocumentVersion(BaseModel):
    version_id: UUID = Field(default_factory=uuid4)
    content: str
    metadata: DocumentMetadata
    comments: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    status: DocumentStatus = DocumentStatus.DRAFT
    metadata: DocumentMetadata
    comments: List[str] = Field(default_factory=list)
    versions: List[DocumentVersion] = Field(default_factory=list)  # Новое поле для версий
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

    def add_version(self, content: str, metadata: DocumentMetadata, comments: List[str]):
        """Добавляет новую версию документа."""
        version = DocumentVersion(content=content, metadata=metadata, comments=comments)
        self.versions.append(version)