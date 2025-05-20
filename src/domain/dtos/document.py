from pydantic import BaseModel, Field, validator
from uuid import UUID
from typing import Optional

class DocumentCreateDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Название документа")
    content: str = Field(..., min_length=1, description="Содержимое документа")

class DocumentUpdateDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Новое название документа")
    content: Optional[str] = Field(None, min_length=1, description="Новое содержимое документа")

    @validator("title", "content", pre=True)
    def prevent_empty_string(cls, v):
        if v == "":
            raise ValueError("Field cannot be an empty string")
        return v

class DocumentListDTO(BaseModel):
    skip: int = Field(..., ge=0, description="Количество документов для пропуска")
    limit: int = Field(..., ge=1, le=100, description="Максимальное количество документов")

class DocumentIdDTO(BaseModel):
    id: UUID = Field(..., description="UUID документа")

    @classmethod
    def from_string(cls, id_str: str) -> "DocumentIdDTO":
        try:
            return cls(id=UUID(id_str))
        except ValueError:
            raise ValueError("Invalid UUID format")