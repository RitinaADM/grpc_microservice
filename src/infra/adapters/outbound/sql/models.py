from beanie import Document as BeanieDocument
from uuid import UUID
from datetime import datetime

class MongoDocument(BeanieDocument):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Settings:
        name = "documents"