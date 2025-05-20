import grpc
from concurrent import futures
from dishka import make_async_container
from src.domain.py_proto import service_pb2, service_pb2_grpc
from src.infra.di.provider import AppProvider
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
import logging
from src.infra.config.logging import setup_logging
from grpc_reflection.v1alpha import reflection
from src.infra.config.settings import settings

async def serve():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting gRPC server...")
    container = make_async_container(AppProvider())
    async with container() as c:
        servicer = await c.get(DocumentServiceServicer)
        server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, server)

        # Включаем gRPC рефлексию
        SERVICE_NAMES = (
            service_pb2.DESCRIPTOR.services_by_name['DocumentService'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)
        logger.info("gRPC reflection enabled for DocumentService")

        server.add_insecure_port(f'[::]:{settings.GRPC_PORT}')
        logger.info(f"gRPC server started on port {settings.GRPC_PORT}")
        await server.start()
        await server.wait_for_termination()

if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())