import pytest
import grpc
import motor.motor_asyncio
from beanie import init_beanie
from src.infra.adapters.outbound.mongo.models import MongoDocument
from src.domain.dtos.document import DocumentCreateDTO, DocumentStatus, DocumentMetadata
from src.infra.adapters.inbound.grpc.py_proto import service_pb2, service_pb2_grpc
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.infra.di.container import make_async_container
from src.di.providers import AppProvider

@pytest.fixture(scope="module")
async def init_test_db():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.test_database, document_models=[MongoDocument])
    yield
    await client.close()

@pytest.fixture(scope="function")
async def grpc_server():
    server = grpc.aio.server()
    container = make_async_container(AppProvider())
    service = await container.get(DocumentServicePort)
    servicer = DocumentServiceServicer(service)
    service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    yield server
    await server.stop(grace=None)

@pytest.mark.asyncio
async def test_integration_create_and_get(init_test_db):
    container = make_async_container(AppProvider())
    async with container() as c:
        service = await c.get(DocumentServicePort)
        create_dto = DocumentCreateDTO(
            title="Integration Test Doc",
            content="Content",
            status=DocumentStatus.DRAFT,
            metadata=DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
            comments=["comment1"]
        )
        created_doc = await service.create(create_dto)
        retrieved_doc = await service.get(created_doc.id)
        assert retrieved_doc.title == "Integration Test Doc"
        assert retrieved_doc.content == "Content"

@pytest.mark.asyncio
async def test_grpc_integration_create_and_get(grpc_server):
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        create_request = service_pb2.CreateDocumentRequest(
            title="GRPC Integration Doc",
            content="Content",
            status=service_pb2.DocumentStatus.DRAFT,
            metadata=service_pb2.DocumentMetadata(author="Author", tags=["tag1"], category="cat"),
            comments=["comment1"]
        )
        create_response = await stub.CreateDocument(create_request)
        get_request = service_pb2.GetDocumentRequest(id=create_response.id)
        get_response = await stub.GetDocument(get_request)
        assert get_response.title == "GRPC Integration Doc"
        assert get_response.content == "Content"