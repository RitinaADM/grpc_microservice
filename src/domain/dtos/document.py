from pydantic import BaseModel, field_validator, ConfigDict
from src.domain.models.document import DocumentStatus
from typing import List, Optional
from uuid import UUID

class DocumentCreateDTO(BaseModel):
    title: str
    content: str
    status: DocumentStatus
    author: str
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    comments: Optional[List[str]] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("comments", mode="before")
    @classmethod
    def validate_comments(cls, comments: Optional[List[str]]) -> Optional[List[str]]:
        if comments:
            for comment in comments:
                if not comment or comment.strip() == "":
                    raise ValueError("Комментарий не может быть пустым")
        return comments

    @field_validator("title", "content", "author", mode="before")
    @classmethod
    def validate_not_empty(cls, value: str, info) -> str:
        if not value or value.strip() == "":
            raise ValueError(f"Поле '{info.field_name}' не может быть пустым")
        return value

class DocumentUpdateDTO(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[DocumentStatus] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    comments: Optional[List[str]] = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("title", "content", "author", mode="before")
    @classmethod
    def validate_not_empty(cls, value: Optional[str], info) -> Optional[str]:
        if value is not None and (not value or value.strip() == ""):
            raise ValueError(f"Поле '{info.field_name}' не может быть пустым")
        return value

    @field_validator("comments", mode="before")
    @classmethod
    def validate_comments(cls, comments: Optional[List[str]]) -> Optional[List[str]]:
        if comments:
            for comment in comments:
                if not comment or comment.strip() == "":
                    raise ValueError("Комментарий не может быть пустым")
        return comments

class DocumentListDTO(BaseModel):
    skip: int = 0
    limit: int = 10

    @field_validator("skip")
    @classmethod
    def validate_skip(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Пропуск должен быть неотрицательным")
        return value

class DocumentIdDTO(BaseModel):
    id: UUID

    @classmethod
    def from_string(cls, id_str: str) -> "DocumentIdDTO":
        try:
            return cls(id=UUID(id_str))
        except ValueError:
            raise ValueError("Неверный формат UUID")