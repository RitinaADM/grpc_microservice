import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload
from src.domain.models.document import Document, DocumentVersion
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.dtos.document import DocumentUpdateDTO
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion
from src.infra.adapters.outbound.sql.mapper import SQLMapper
from src.domain.exceptions.base import BaseAppException


class SQLDocumentAdapter(DocumentRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.logger = logging.getLogger(__name__)
        self.mapper = SQLMapper()

    def _convert_uuid_to_str(self, obj):
        """Recursively convert UUID objects to strings for JSON serialization."""
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._convert_uuid_to_str(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_uuid_to_str(item) for item in obj]
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    async def get_by_id(self, id: UUID) -> Optional[Document]:
        self.logger.debug(f"Getting document from PostgreSQL with ID: {id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_doc = result.scalars().first()
                    return self.mapper.to_domain_document(sql_doc) if sql_doc else None
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while fetching document {id}: {str(e)}")
            raise BaseAppException(f"Failed to fetch document due to database error: {str(e)}")

    async def create(self, document: Document) -> Document:
        self.logger.debug(f"Creating document in PostgreSQL: {document.id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    sql_doc = self.mapper.to_sql_document(document)
                    session.add(sql_doc)
                    await session.flush()
                    return document
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while creating document {document.id}: {str(e)}")
            raise BaseAppException(f"Failed to create document due to database error: {str(e)}")

    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        self.logger.debug(f"Updating document in PostgreSQL with ID: {id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_doc = result.scalars().first()
                    if not sql_doc:
                        self.logger.warning(f"Document with ID: {id} not found or deleted")
                        return None

                    # Create version with JSON-serializable data
                    document_dict = self.mapper.to_domain_document(sql_doc).dict()
                    serializable_document_dict = self._convert_uuid_to_str(document_dict)

                    current_version = SQLDocumentVersion(
                        version_id=uuid4(),
                        document_id=sql_doc.id,
                        document_data=serializable_document_dict,
                        timestamp=datetime.utcnow()
                    )
                    self.logger.debug(f"Creating version {current_version.version_id} for document {id}")
                    sql_doc.versions.append(current_version)

                    # Update document fields
                    if data.title is not None:
                        sql_doc.title = data.title
                    if data.content is not None:
                        sql_doc.content = data.content
                    if data.status is not None:
                        sql_doc.status = data.status
                    if data.author is not None:
                        sql_doc.author = data.author
                    if data.tags is not None:
                        sql_doc.tags = data.tags
                    if data.category is not None:
                        sql_doc.category = data.category
                    if data.comments is not None:
                        sql_doc.comments = data.comments
                    sql_doc.updated_at = datetime.utcnow()
                    await session.flush()
                    return self.mapper.to_domain_document(sql_doc)
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while updating document {id}: {str(e)}")
            raise BaseAppException(f"Failed to update document due to database error: {str(e)}")
        except TypeError as e:
            self.logger.error(f"JSON serialization error while updating document {id}: {str(e)}")
            raise BaseAppException(f"Failed to serialize document data: {str(e)}")

    async def delete(self, id: UUID) -> bool:
        self.logger.debug(f"Soft deleting document from PostgreSQL with ID: {id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_doc = result.scalars().first()
                    if not sql_doc:
                        self.logger.warning(f"Document with ID: {id} not found")
                        return False
                    sql_doc.is_deleted = True
                    sql_doc.updated_at = datetime.utcnow()
                    await session.flush()
                    return True
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while deleting document {id}: {str(e)}")
            raise BaseAppException(f"Failed to delete document due to database error: {str(e)}")

    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        self.logger.debug(f"Listing documents from PostgreSQL with skip: {skip}, limit: {limit}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.is_deleted == False)
                        .offset(skip)
                        .limit(limit)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_docs = result.scalars().all()
                    return [self.mapper.to_domain_document(doc) for doc in sql_docs]
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while listing documents: {str(e)}")
            raise BaseAppException(f"Failed to list documents due to database error: {str(e)}")

    async def restore(self, id: UUID) -> Optional[Document]:
        self.logger.debug(f"Restoring document in PostgreSQL with ID: {id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id, SQLDocument.is_deleted == True)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_doc = result.scalars().first()
                    if not sql_doc:
                        self.logger.warning(f"Document with ID: {id} not found or not deleted")
                        return None
                    sql_doc.is_deleted = False
                    sql_doc.updated_at = datetime.utcnow()
                    await session.flush()
                    return self.mapper.to_domain_document(sql_doc)
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while restoring document {id}: {str(e)}")
            raise BaseAppException(f"Failed to restore document due to database error: {str(e)}")

    async def get_versions(self, id: UUID) -> List[DocumentVersion]:
        self.logger.debug(f"Getting versions for document from PostgreSQL with ID: {id}")
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id)
                        .options(selectinload(SQLDocument.versions))
                    )
                    sql_doc = result.scalars().first()
                    return [self.mapper.to_domain_version(v) for v in sql_doc.versions] if sql_doc else []
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL error while fetching versions for document {id}: {str(e)}")
            raise BaseAppException(f"Failed to fetch versions due to database error: {str(e)}")