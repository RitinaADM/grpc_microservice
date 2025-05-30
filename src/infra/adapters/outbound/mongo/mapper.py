from typing import Optional
from src.domain.models.document import Document
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.ports.outbound.mappers.base import BaseMapper

class MongoMapper(BaseMapper[Document]):
    """Маппер для преобразования между доменными объектами Document и MongoDocument."""

    def to_domain_document(self, mongo_doc: Optional[MongoDocument]) -> Optional[Document]:
        """Преобразует MongoDocument в доменный Document."""
        if not mongo_doc:
            return None
        return Document(
            id=self._deserialize_uuid(mongo_doc.id),
            title=mongo_doc.title,
            content=mongo_doc.content,
            status=mongo_doc.status,
            author=mongo_doc.author,
            tags=mongo_doc.tags or [],
            category=mongo_doc.category,
            comments=mongo_doc.comments or [],
            versions=mongo_doc.versions,
            created_at=mongo_doc.created_at,
            updated_at=mongo_doc.updated_at,
            is_deleted=mongo_doc.is_deleted
        )

    def to_mongo_document(self, document: Document) -> MongoDocument:
        """Преобразует доменный Document в MongoDocument."""
        return MongoDocument(
            id=self._deserialize_uuid(document.id),
            title=document.title,
            content=document.content,
            status=document.status,
            author=document.author,
            tags=document.tags or [],
            category=document.category,
            comments=document.comments or [],
            versions=document.versions,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_deleted=document.is_deleted
        )

    def to_storage(self, document: Document) -> MongoDocument:
        """Сериализует Document в MongoDocument."""
        return self.to_mongo_document(document)

    def from_storage(self, data: Optional[MongoDocument]) -> Optional[Document]:
        """Десериализует MongoDocument в Document."""
        return self.to_domain_document(data)