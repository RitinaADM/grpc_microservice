from pydantic import BaseModel, Field, UUID4
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from typing import List, Optional

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    status: DocumentStatus = DocumentStatus.DRAFT
    author: str = Field(..., min_length=1, max_length=100)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    comments: List[str] = Field(default_factory=list)
    versions: List['DocumentVersion'] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

    class Config:
        json_encoders = {
            UUID4: str  # Преобразует UUID в строку при сериализации в JSON
        }

class DocumentVersion(BaseModel):
    version_id: UUID = Field(default_factory=uuid4)
    document: Document
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID4: str  # Преобразует UUID в строку при сериализации в JSON
        }