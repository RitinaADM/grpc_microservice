from pydantic import BaseModel, Field, validator
from uuid import UUID
from typing import Optional, List
from src.domain.models.document import DocumentStatus, DocumentMetadata

from pydantic import BaseModel, field_validator
from typing import List

class DocumentCreateDTO(BaseModel):
    title: str
    content: str
    status: DocumentStatus
    metadata: DocumentMetadata
    comments: List[str]

    @field_validator("comments", mode="before")
    @classmethod
    def check_comments_not_empty(cls, v: List[str]) -> List[str]:
        for comment in v:
            if not comment.strip():
                raise ValueError("Comment cannot be empty")
        return v

    @field_validator("title", "content", mode="before")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v

class DocumentUpdateDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[DocumentStatus] = None
    metadata: Optional[DocumentMetadata] = None
    comments: Optional[List[str]] = None

    @validator("title", "content", pre=True)
    def prevent_empty_string(cls, v):
        if v == "":
            raise ValueError("Поле не может быть пустой строкой")
        return v

    @validator("comments", each_item=True, pre=True)
    def check_non_empty_comments(cls, v):
        if v and not v.strip():
            raise ValueError("Комментарий не может быть пустым или состоять только из пробелов")
        return v

class DocumentListDTO(BaseModel):
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)

class DocumentIdDTO(BaseModel):
    id: UUID = Field(..., description="UUID документа")

    @classmethod
    def from_string(cls, id_str: str) -> "DocumentIdDTO":
        try:
            return cls(id=UUID(id_str))
        except ValueError:
            raise ValueError("Неверный формат UUID")