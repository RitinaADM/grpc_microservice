from typing import Optional
from src.domain.models.document import Document
from src.infra.adapters.outbound.mongo.models import MongoDocument

class MongoMapper:
    @staticmethod
    def to_domain_document(mongo_doc: Optional[MongoDocument]) -> Optional[Document]:
        if not mongo_doc:
            return None
        return Document(
            id=mongo_doc.id,
            title=mongo_doc.title,
            content=mongo_doc.content,
            status=mongo_doc.status,
            author=mongo_doc.author,
            tags=mongo_doc.tags,
            category=mongo_doc.category,
            comments=mongo_doc.comments,
            versions=mongo_doc.versions,
            created_at=mongo_doc.created_at,
            updated_at=mongo_doc.updated_at,
            is_deleted=mongo_doc.is_deleted
        )

    @staticmethod
    def to_mongo_document(document: Document) -> MongoDocument:
        return MongoDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            status=document.status,
            author=document.author,
            tags=document.tags,
            category=document.category,
            comments=document.comments,
            versions=document.versions,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_deleted=document.is_deleted
        )