from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion, DocumentStatus
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion

class SQLMapper:
    @staticmethod
    def to_domain_document(sql_document: SQLDocument) -> Document:
        if not sql_document:
            return None
        return Document(
            id=sql_document.id,
            title=sql_document.title,
            content=sql_document.content,
            status=DocumentStatus(sql_document.status),
            author=sql_document.author,
            tags=sql_document.tags or [],
            category=sql_document.category,
            comments=sql_document.comments or [],
            created_at=sql_document.created_at,
            updated_at=sql_document.updated_at,
            is_deleted=sql_document.is_deleted,
            versions=[SQLMapper.to_domain_version(v) for v in sql_document.versions]
        )

    @staticmethod
    def to_domain_version(sql_version: SQLDocumentVersion) -> DocumentVersion:
        document_data = sql_version.document_data
        # Ensure UUID and datetime fields are properly converted
        document_data['id'] = UUID(document_data['id'])
        document_data['created_at'] = datetime.fromisoformat(document_data['created_at'])
        document_data['updated_at'] = datetime.fromisoformat(document_data['updated_at'])
        document_data['status'] = DocumentStatus(document_data['status'])
        document_data['tags'] = document_data.get('tags', [])
        document_data['comments'] = document_data.get('comments', [])
        document_data['versions'] = []  # Versions are not nested in document_data
        return DocumentVersion(
            version_id=sql_version.version_id,
            document=Document(**document_data),
            timestamp=sql_version.timestamp
        )

    @staticmethod
    def to_sql_document(document: Document) -> SQLDocument:
        return SQLDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            status=document.status.value,
            author=document.author,
            tags=document.tags or [],
            category=document.category,
            comments=document.comments or [],
            created_at=document.created_at or datetime.utcnow(),
            updated_at=document.updated_at or datetime.utcnow(),
            is_deleted=document.is_deleted
        )