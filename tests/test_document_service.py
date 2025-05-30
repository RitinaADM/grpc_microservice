import pytest
from uuid import uuid4
from datetime import datetime
from src.domain.models.document import Document, DocumentStatus, DocumentMetadata
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.application.document.service import DocumentService
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.exceptions.base import BaseAppException
from pymongo.errors import ConnectionFailure

@pytest.mark.asyncio
async def test_get_by_id_success():
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="Test Doc",
        content="Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockRepository:
        async def get_by_id(self, id):
            return mock_document if id == document_id else None

    class MockCache:
        async def get_document(self, id):
            return None
        async def set_document(self, document):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)
    result = await service.get_by_id(id_dto)

    assert result == mock_document
    assert result.title == "Test Doc"

@pytest.mark.asyncio
async def test_get_by_id_not_found():
    document_id = uuid4()

    class MockRepository:
        async def get_by_id(self, id):
            return None

    class MockCache:
        async def get_document(self, id):
            return None

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)

    with pytest.raises(DocumentNotFoundException):
        await service.get_by_id(id_dto)

@pytest.mark.asyncio
async def test_get_by_id_db_error():
    document_id = uuid4()

    class MockRepository:
        async def get_by_id(self, id):
            raise ConnectionFailure("Database error")

    class MockCache:
        async def get_document(self, id):
            return None

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)

    with pytest.raises(BaseAppException, match="Database error"):
        await service.get_by_id(id_dto)

@pytest.mark.asyncio
async def test_create_document_success():
    mock_document = Document(
        id=uuid4(),
        title="New Doc",
        content="New Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockRepository:
        async def create(self, document):
            return mock_document

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    create_dto = DocumentCreateDTO(
        title="New Doc",
        content="New Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"]
    )
    result = await service.create(create_dto)

    assert result.title == "New Doc"
    assert result.id == mock_document.id

@pytest.mark.asyncio
async def test_create_document_db_error():
    class MockRepository:
        async def create(self, document):
            raise ConnectionFailure("Database error")

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    create_dto = DocumentCreateDTO(
        title="New Doc",
        content="New Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"]
    )

    with pytest.raises(BaseAppException, match="Database error"):
        await service.create(create_dto)

@pytest.mark.asyncio
async def test_update_document_success():
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="Updated Doc",
        content="Updated Content",
        status=DocumentStatus.PUBLISHED,
        metadata=DocumentMetadata(author="Author", tags=["tag2"], category="new_cat"),
        comments=["comment2"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockRepository:
        async def update(self, id, data):
            return mock_document if id == document_id else None

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)
    update_dto = DocumentUpdateDTO(
        title="Updated Doc",
        content="Updated Content",
        status=DocumentStatus.PUBLISHED,
        metadata=DocumentMetadata(author="Author", tags=["tag2"], category="new_cat"),
        comments=["comment2"]
    )
    result = await service.update(id_dto, update_dto)

    assert result.title == "Updated Doc"
    assert result.status == DocumentStatus.PUBLISHED

@pytest.mark.asyncio
async def test_update_document_not_found():
    document_id = uuid4()

    class MockRepository:
        async def update(self, id, data):
            return None

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)
    update_dto = DocumentUpdateDTO(title="Updated Doc")

    with pytest.raises(DocumentNotFoundException):
        await service.update(id_dto, update_dto)

@pytest.mark.asyncio
async def test_delete_document_success():
    document_id = uuid4()

    class MockRepository:
        async def delete(self, id):
            return True if id == document_id else False

    class MockCache:
        async def invalidate_document(self, document_id):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)
    result = await service.delete(id_dto)

    assert result == True

@pytest.mark.asyncio
async def test_delete_document_not_found():
    document_id = uuid4()

    class MockRepository:
        async def delete(self, id):
            return False

    class MockCache:
        async def invalidate_document(self, document_id):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)

    with pytest.raises(DocumentNotFoundException):
        await service.delete(id_dto)

@pytest.mark.asyncio
async def test_restore_document_success():
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="Restored Doc",
        content="Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockRepository:
        async def restore(self, id):
            return mock_document if id == document_id else None

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)
    result = await service.restore(id_dto)

    assert result.is_deleted == False
    assert result.title == "Restored Doc"

@pytest.mark.asyncio
async def test_restore_document_not_found():
    document_id = uuid4()

    class MockRepository:
        async def restore(self, id):
            return None

    class MockCache:
        async def set_document(self, document):
            pass
        async def invalidate_document_list(self):
            pass

    service = DocumentService(MockRepository(), MockCache())
    id_dto = DocumentIdDTO(id=document_id)

    with pytest.raises(DocumentNotFoundException):
        await service.restore(id_dto)

@pytest.mark.asyncio
async def test_list_documents_success():
    document_id1 = uuid4()
    document_id2 = uuid4()
    mock_documents = [
        Document(
            id=document_id1,
            title="Doc1",
            content="Content1",
            status=DocumentStatus.DRAFT,
            metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
            comments=["comment1"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_deleted=False
        ),
        Document(
            id=document_id2,
            title="Doc2",
            content="Content2",
            status=DocumentStatus.PUBLISHED,
            metadata=DocumentMetadata(author="Author", tags=["tag2"], category="cat"),
            comments=["comment2"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_deleted=False
        )
    ]

    class MockRepository:
        async def list_documents(self, skip, limit):
            return mock_documents

    class MockCache:
        async def get_document_list(self, skip, limit):
            return None
        async def set_document_list(self, documents, skip, limit):
            pass

    service = DocumentService(MockRepository(), MockCache())
    list_dto = DocumentListDTO(skip=0, limit=10)
    result = await service.list_documents(list_dto)

    assert len(result) == 2
    assert result[0].title == "Doc1"
    assert result[1].title == "Doc2"

@pytest.mark.asyncio
async def test_list_documents_empty():
    class MockRepository:
        async def list_documents(self, skip, limit):
            return []

    class MockCache:
        async def get_document_list(self, skip, limit):
            return None
        async def set_document_list(self, documents, skip, limit):
            pass

    service = DocumentService(MockRepository(), MockCache())
    list_dto = DocumentListDTO(skip=0, limit=10)
    result = await service.list_documents(list_dto)

    assert len(result) == 0