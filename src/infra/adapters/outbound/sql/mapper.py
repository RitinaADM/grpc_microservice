from datetime import datetime
from typing import Optional

from src.domain.models.document import Document, DocumentVersion
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion
from src.domain.ports.outbound.mappers.base import BaseMapper
from src.infra.adapters.outbound.mappers.utils import MapperUtils, VersionMapper

class SQLMapper(BaseMapper[Document]):
    """Маппер для преобразования между доменными объектами Document и SQLDocument."""

    def to_domain_document(self, sql_document: SQLDocument) -> Optional[Document]:
        """Преобразует SQLDocument в доменный Document."""
        if not sql_document:
            return None
        doc_dict = {
            'id': sql_document.id,
            'title': sql_document.title,
            'content': sql_document.content,
            'status': sql_document.status,
            'author': sql_document.author,
            'tags': list(sql_document.tags) if sql_document.tags else [],
            'category': sql_document.category,
            'comments': list(sql_document.comments) if sql_document.comments else [],
            'created_at': sql_document.created_at,
            'updated_at': sql_document.updated_at,
            'is_deleted': sql_document.is_deleted,
            'versions': [VersionMapper.to_domain_version(v, "sql") for v in sql_document.versions]
        }
        doc_dict['id'] = MapperUtils.deserialize_uuid(doc_dict['id'])
        doc_dict['created_at'] = MapperUtils.deserialize_datetime(doc_dict['created_at'])
        doc_dict['updated_at'] = MapperUtils.deserialize_datetime(doc_dict['updated_at'])
        doc_dict['status'] = MapperUtils.deserialize_status(doc_dict['status'])
        return Document(**doc_dict)

    def to_sql_document(self, document: Document) -> SQLDocument:
        """Преобразует доменный Document в SQLDocument."""
        return SQLDocument(
            id=MapperUtils.deserialize_uuid(document.id),
            title=document.title,
            content=document.content,
            status=MapperUtils.serialize_status(document.status),
            author=document.author,
            tags=document.tags or [],
            category=document.category,
            comments=document.comments or [],
            created_at=document.created_at or datetime.utcnow(),
            updated_at=document.updated_at or datetime.utcnow(),
            is_deleted=document.is_deleted
        )

    def to_storage(self, document: Document) -> dict:
        """Сериализует Document в JSON-сериализуемый словарь для JSONB."""
        return MapperUtils.to_json_serializable(document)

    def from_storage(self, data: SQLDocument) -> Document:
        """Десериализует SQLDocument в Document."""
        return self.to_domain_document(data)