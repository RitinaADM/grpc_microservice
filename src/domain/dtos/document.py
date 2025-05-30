from pydantic import BaseModel, Field, validator
from uuid import UUID
from typing import Optional, List
from src.domain.models.document import DocumentStatus

class DocumentCreateDTO(BaseModel):
    title: str
    content: str
    status: DocumentStatus
    author: str = Field(..., min_length=1, max_length=100)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    comments: List[str] = Field(default_factory=list)

    @validator("comments", each_item=True, pre=True)
    def check_comments_not_empty(cls, v):
        if v and not v.strip():
            raise ValueError("Comment cannot be empty")
        return v

    @validator("title", "content", "author", pre=True)
    def check_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v

class DocumentUpdateDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[DocumentStatus] = None
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    comments: Optional[List[str]] = None

    @validator("title", "content", "author", pre=True)
    def prevent_empty_string(cls, v):
        if v == "":
            raise ValueError("Field cannot be empty")
        return v

    @validator("comments", each_item=True, pre=True)
    def check_non_empty_comments(cls, v):
        if v and not v.strip():
            raise ValueError("Comment cannot be empty")
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
            raise ValueError("Invalid UUID format")