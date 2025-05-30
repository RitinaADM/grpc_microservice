from uuid import UUID
from datetime import datetime
from src.domain.models.document import Document, DocumentVersion, DocumentStatus, DocumentMetadata
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion

class SQLMapper:
    """Маппер для преобразования SQL-моделей в доменные и обратно."""

    @staticmethod
    def to_domain_document(sql_doc: SQLDocument) -> Document:
        """
        Преобразует SQLDocument в доменную модель Document.

        Args:
            sql_doc: SQL-модель документа.

        Returns:
            Document: Доменная модель документа без версий.
        """
        return Document(
            id=sql_doc.id,
            title=sql_doc.title,
            content=sql_doc.content,
            status=DocumentStatus(sql_doc.status),
            metadata=DocumentMetadata(
                author=sql_doc.document_metadata.get('author', ''),
                tags=sql_doc.document_metadata.get('tags', []),
                category=sql_doc.document_metadata.get('category', None)
            ),
            comments=sql_doc.comments,
            versions=[],  # Explicitly set versions to empty list to exclude them
            created_at=sql_doc.created_at,
            updated_at=sql_doc.updated_at,
            is_deleted=sql_doc.is_deleted
        )

    @staticmethod
    def to_domain_version(sql_version: SQLDocumentVersion) -> DocumentVersion:
        """
        Преобразует SQLDocumentVersion в доменную модель DocumentVersion.

        Args:
            sql_version: SQL-модель версии документа.

        Returns:
            DocumentVersion: Доменная модель версии документа.
        """
        return DocumentVersion(
            version_id=sql_version.version_id,
            content=sql_version.content,
            metadata=DocumentMetadata(
                author=sql_version.document_metadata.get('author', ''),
                tags=sql_version.document_metadata.get('tags', []),
                category=sql_version.document_metadata.get('category', None)
            ),
            comments=sql_version.comments,
            timestamp=sql_version.timestamp
        )

    @staticmethod
    def to_sql_document(document: Document) -> SQLDocument:
        """
        Преобразует доменную модель Document в SQLDocument.

        Args:
            document: Доменная модель документа.

        Returns:
            SQLDocument: SQL-модель документа.
        """
        return SQLDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            status=document.status.value,
            document_metadata={
                'author': document.metadata.author,
                'tags': document.metadata.tags,
                'category': document.metadata.category
            },
            comments=document.comments,
            created_at=document.created_at or datetime.utcnow(),
            updated_at=document.updated_at or datetime.utcnow(),
            is_deleted=document.is_deleted
        )

    @staticmethod
    def to_sql_version(version: DocumentVersion, document_id: UUID) -> SQLDocumentVersion:
        """
        Преобразует доменную модель DocumentVersion в SQLDocumentVersion.

        Args:
            version: Доменная модель версии документа.
            document_id: UUID документа, к которому относится версия.

        Returns:
            SQLDocumentVersion: SQL-модель версии документа.
        """
        return SQLDocumentVersion(
            version_id=version.version_id,
            document_id=document_id,
            content=version.content,
            document_metadata={
                'author': version.metadata.author,
                'tags': version.metadata.tags,
                'category': version.metadata.category
            },
            comments=version.comments,
            timestamp=version.timestamp or datetime.utcnow()
        )