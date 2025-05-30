import pytest
import grpc
from src.infra.adapters.inbound.grpc.py_proto import service_pb2, service_pb2_grpc
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.domain.models.document import Document, DocumentStatus, DocumentMetadata
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from src.domain.exceptions.document import DocumentNotFoundException
from uuid import uuid4
from datetime import datetime

@pytest.fixture
async def grpc_server():
    server = grpc.aio.server()
    server.add_insecure_port('[::]:50051')
    yield server
    await server.stop(None)

@pytest.mark.asyncio
async def test_get_document_success(grpc_server):
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

    class MockService:
        async def get_by_id(self, id_dto):
            return mock_document

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.GetDocumentRequest(id=str(document_id))
        response = await stub.GetDocument(request)

        assert response.id == str(document_id)
        assert response.title == "Test Doc"
        assert response.status == service_pb2.DocumentStatus.DRAFT

@pytest.mark.asyncio
async def test_get_document_not_found(grpc_server):
    class MockService:
        async def get_by_id(self, id_dto):
            raise DocumentNotFoundException()

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.GetDocumentRequest(id=str(uuid4()))

        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.GetDocument(request)
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

@pytest.mark.asyncio
async def test_create_document_success(grpc_server):
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="New Doc",
        content="Content",
        status=DocumentStatus.DRAFT,
        metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
        comments=["comment1"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockService:
        async def create(self, data):
            return mock_document

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.CreateDocumentRequest(
            title="New Doc",
            content="Content",
            status=service_pb2.DocumentStatus.DRAFT,
            metadata=service_pb2.DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
            comments=["comment1"]
        )
        response = await stub.CreateDocument(request)

        assert response.id == str(document_id)
        assert response.title == "New Doc"

@pytest.mark.asyncio
async def test_create_document_invalid_data(grpc_server):
    class MockService:
        async def create(self, data):
            raise ValueError("Title cannot be empty")

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.CreateDocumentRequest(title="", content="Content")

        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.CreateDocument(request)
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT

@pytest.mark.asyncio
async def test_update_document_success(grpc_server):
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="Updated Doc",
        content="New Content",
        status=DocumentStatus.PUBLISHED,
        metadata=DocumentMetadata(author="Author", tags=["tag2"], category="new_cat"),
        comments=["comment2"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )

    class MockService:
        async def update(self, id_dto, data):
            return mock_document

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.UpdateDocumentRequest(
            id=str(document_id),
            title="Updated Doc",
            content="New Content",
            status=service_pb2.DocumentStatus.PUBLISHED,
            metadata=service_pb2.DocumentMetadata(author="Author", tags=["tag2"], category="new_cat"),
            comments=["comment2"]
        )
        response = await stub.UpdateDocument(request)

        assert response.title == "Updated Doc"
        assert response.status == service_pb2.DocumentStatus.PUBLISHED

@pytest.mark.asyncio
async def test_update_document_not_found(grpc_server):
    class MockService:
        async def update(self, id_dto, data):
            raise DocumentNotFoundException()

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.UpdateDocumentRequest(id=str(uuid4()), title="Updated Doc")

        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.UpdateDocument(request)
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

@pytest.mark.asyncio
async def test_delete_document_success(grpc_server):
    document_id = uuid4()

    class MockService:
        async def delete(self, id_dto):
            return True

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.DeleteDocumentRequest(id=str(document_id))
        response = await stub.DeleteDocument(request)

        assert response.success == True

@pytest.mark.asyncio
async def test_delete_document_not_found(grpc_server):
    class MockService:
        async def delete(self, id_dto):
            raise DocumentNotFoundException()

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.DeleteDocumentRequest(id=str(uuid4()))

        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.DeleteDocument(request)
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

@pytest.mark.asyncio
async def test_restore_document_success(grpc_server):
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

    class MockService:
        async def restore(self, id_dto):
            return mock_document

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.RestoreDocumentRequest(id=str(document_id))
        response = await stub.RestoreDocument(request)

        assert response.id == str(document_id)
        assert response.is_deleted == False

@pytest.mark.asyncio
async def test_restore_document_not_found(grpc_server):
    class MockService:
        async def restore(self, id_dto):
            raise DocumentNotFoundException()

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.RestoreDocumentRequest(id=str(uuid4()))

        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.RestoreDocument(request)
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

@pytest.mark.asyncio
async def test_list_documents_success(grpc_server):
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

    class MockService:
        async def list_documents(self, params):
            return mock_documents

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.ListDocumentsRequest(skip=0, limit=10)
        response = await stub.ListDocuments(request)

        assert len(response.documents) == 2
        assert response.documents[0].title == "Doc1"
        assert response.documents[1].title == "Doc2"

@pytest.mark.asyncio
async def test_list_documents_empty(grpc_server):
    class MockService:
        async def list_documents(self, params):
            return []

    servicer = DocumentServiceServicer(MockService())
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, grpc_server)
    await grpc_server.start()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        request = service_pb2.ListDocumentsRequest(skip=0, limit=10)
        response = await stub.ListDocuments(request)

        assert len(response.documents) == 0