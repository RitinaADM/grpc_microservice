import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.domain.dtos.document import DocumentUpdateDTO
from src.infra.adapters.outbound.sql.adapter import SQLDocumentAdapter
from src.domain.models.document import Document, DocumentStatus
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_document():
    engine = create_async_engine("postgresql+asyncpg://user:password@postgres:5432/microservice_db")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    adapter = SQLDocumentAdapter(session_factory)
    document = Document(
        id=uuid4(),
        title="Test",
        content="Content",
        status=DocumentStatus.DRAFT,
        author="Author"
    )
    created_doc = await adapter.create(document)
    assert created_doc.id == document.id
    fetched_doc = await adapter.get_by_id(document.id)
    assert fetched_doc.title == "Test"
    await engine.dispose()

@pytest.mark.asyncio
async def test_update_document():
    engine = create_async_engine("postgresql+asyncpg://user:password@postgres:5432/microservice_db")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    adapter = SQLDocumentAdapter(session_factory)
    document = Document(
        id=uuid4(),
        title="Original",
        content="Content",
        status=DocumentStatus.DRAFT,
        author="Author"
    )
    await adapter.create(document)
    update_dto = DocumentUpdateDTO(title="Updated")
    updated_doc = await adapter.update(document.id, update_dto)
    assert updated_doc.title == "Updated"
    assert len(updated_doc.versions) == 1
    await engine.dispose()

@pytest.mark.asyncio
async def test_delete_restore_document():
    engine = create_async_engine("postgresql+asyncpg://user:password@postgres:5432/microservice_db")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    adapter = SQLDocumentAdapter(session_factory)
    document = Document(
        id=uuid4(),
        title="Test",
        content="Content",
        status=DocumentStatus.DRAFT,
        author="Author"
    )
    await adapter.create(document)
    success = await adapter.delete(document.id)
    assert success is True
    fetched_doc = await adapter.get_by_id(document.id)
    assert fetched_doc is None
    restored_doc = await adapter.restore(document.id)
    assert restored_doc.is_deleted is False
    await engine.dispose()