from sqlalchemy import Column, String, Boolean, DateTime, func, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from uuid import uuid4
from src.domain.models.document import DocumentStatus

Base = declarative_base()

class SQLDocumentVersion(Base):
    __tablename__ = "document_versions"
    version_id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(SQLUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content = Column(String, nullable=False)
    document_metadata = Column(JSON, nullable=False)
    comments = Column(ARRAY(String), nullable=False, default=lambda: [])
    timestamp = Column(DateTime, default=func.now())

class SQLDocument(Base):
    __tablename__ = "documents"
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT)
    document_metadata = Column(JSON, nullable=False)
    comments = Column(ARRAY(String), nullable=False, default=lambda: [])
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    versions = relationship("SQLDocumentVersion", backref="document")