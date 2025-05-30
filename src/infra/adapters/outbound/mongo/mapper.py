from typing import Optional
from src.domain.models.document import Document
from src.infra.adapters.outbound.mongo.models import MongoDocument

class MongoMapper:
    """Маппер для преобразования между Mongo-моделями и доменными моделями."""

    @staticmethod
    def to_domain_document(mongo_doc: Optional[MongoDocument]) -> Optional[Document]:
        """
        Преобразует MongoDocument в доменную модель Document.

        Args:
            mongo_doc: Mongo-модель документа.

        Returns:
            Document: Доменная модель документа, если mongo_doc не None.
            None: Если mongo_doc равен None.
        """
        if not mongo_doc:
            return None
        return Document(
            id=mongo_doc.id,
            title=mongo_doc.title,
            content=mongo_doc.content,
            status=mongo_doc.status,
            metadata=mongo_doc.metadata,
            comments=mongo_doc.comments,
            versions=mongo_doc.versions,
            created_at=mongo_doc.created_at,
            updated_at=mongo_doc.updated_at,
            is_deleted=mongo_doc.is_deleted
        )

    @staticmethod
    def to_mongo_document(document: Document) -> MongoDocument:
        """
        Преобразует доменную модель Document в MongoDocument.

        Args:
            document: Доменная модель документа.

        Returns:
            MongoDocument: Mongo-модель документа.
        """
        return MongoDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            status=document.status,
            metadata=document.metadata,
            comments=document.comments,
            versions=document.versions,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_deleted=document.is_deleted
        )