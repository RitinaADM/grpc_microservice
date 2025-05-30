from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, ARRAY, JSONB
from sqlalchemy.orm import declarative_base, relationship
from uuid import uuid4
from src.domain.models.document import DocumentStatus

Base = declarative_base()

class SQLDocumentVersion(Base):
    __tablename__ = "document_versions"
    version_id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(SQLUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    document_data = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, default=func.now())

class SQLDocument(Base):
    __tablename__ = "documents"
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    status = Column(String, nullable=False, default=DocumentStatus.DRAFT.value)
    author = Column(String(100), nullable=False)
    tags = Column(ARRAY(String), nullable=False, default=lambda: [])
    category = Column(String, nullable=True)
    comments = Column(ARRAY(String), nullable=False, default=lambda: [])
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    versions = relationship("SQLDocumentVersion", backref="document")