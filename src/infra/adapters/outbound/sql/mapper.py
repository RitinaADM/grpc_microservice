from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion, DocumentStatus
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion
from src.domain.ports.outbound.mappers.base import BaseMapper

class SQLMapper(BaseMapper[Document]):
    """Маппер для преобразования между доменными объектами Document и SQLDocument."""

    def to_domain_document(self, sql_document: SQLDocument) -> Document:
        """Преобразует SQLDocument в доменный Document."""
        if not sql_document:
            return None
        return Document(
            id=self._deserialize_uuid(sql_document.id),
            title=sql_document.title,
            content=sql_document.content,
            status=self._deserialize_status(sql_document.status),
            author=sql_document.author,
            tags=sql_document.tags or [],
            category=sql_document.category,
            comments=sql_document.comments or [],
            created_at=sql_document.created_at,
            updated_at=sql_document.updated_at,
            is_deleted=sql_document.is_deleted,
            versions=[self.to_domain_version(v) for v in sql_document.versions]
        )

    def to_domain_version(self, sql_version: SQLDocumentVersion) -> DocumentVersion:
        """Преобразует SQLDocumentVersion в доменную DocumentVersion."""
        document_data = sql_version.document_data
        document_data['id'] = self._deserialize_uuid(document_data['id'])
        document_data['created_at'] = self._deserialize_datetime(document_data['created_at'])
        document_data['updated_at'] = self._deserialize_datetime(document_data['updated_at'])
        document_data['status'] = self._deserialize_status(document_data['status'])
        document_data['tags'] = document_data.get('tags', [])
        document_data['comments'] = document_data.get('comments', [])
        document_data['versions'] = []  # Versions are not nested in document_data
        return DocumentVersion(
            version_id=self._deserialize_uuid(sql_version.version_id),
            document=Document(**document_data),
            timestamp=sql_version.timestamp
        )

    def to_sql_document(self, document: Document) -> SQLDocument:
        """Преобразует доменный Document в SQLDocument."""
        return SQLDocument(
            id=self._deserialize_uuid(document.id),
            title=document.title,
            content=document.content,
            status=self._serialize_status(document.status),
            author=document.author,
            tags=document.tags or [],
            category=document.category,
            comments=document.comments or [],
            created_at=document.created_at or datetime.utcnow(),
            updated_at=document.updated_at or datetime.utcnow(),
            is_deleted=document.is_deleted
        )

    def to_storage(self, document: Document) -> SQLDocument:
        """Сериализует Document в SQLDocument."""
        return self.to_sql_document(document)

    def from_storage(self, data: SQLDocument) -> Document:
        """Десериализует SQLDocument в Document."""
        return self.to_domain_document(data)