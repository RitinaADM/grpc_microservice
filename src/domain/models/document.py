from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False