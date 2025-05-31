import asyncio
import logging
import grpc
from grpc_reflection.v1alpha import reflection
from dishka import make_async_container
from src.infra.di.provider import AppProvider
from src.infra.adapters.inbound.grpc.py_proto import service_pb2, service_pb2_grpc
from src.infra.adapters.inbound.grpc.adapter import DocumentServiceServicer
from src.infra.config.settings import settings
from src.infra.config.logging import setup_logging
from src.infra.auth.interceptor import JWTAuthInterceptor

async def serve():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting gRPC server...")

    container = make_async_container(AppProvider())
    try:
        logger.debug(f"Получение DocumentServiceServicer из DI-контейнера, event loop: {asyncio.get_running_loop()}")
        # Создаем временный контекст запроса для получения сервисера
        async with container() as request_container:
            servicer = await request_container.get(DocumentServiceServicer)
        server = grpc.aio.server(interceptors=[JWTAuthInterceptor()])

        # Добавляем сервисер
        service_pb2_grpc.add_DocumentServiceServicer_to_server(servicer, server)

        # Включаем gRPC рефлексию
        SERVICE_NAMES = (
            service_pb2.DESCRIPTOR.services_by_name['DocumentService'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)
        logger.info("gRPC reflection enabled for DocumentService")

        # Запускаем сервер
        server.add_insecure_port(f'[::]:{settings.GRPC_PORT}')
        logger.info(f"gRPC server started on port {settings.GRPC_PORT}")
        await server.start()
        await server.wait_for_termination()
    except Exception as e:
        logger.error(f"Error starting gRPC server: {str(e)}", exc_info=True)
        raise
    finally:
        # Закрываем контейнер и ресурсы
        await container.close()
        logger.info("DI container closed")

if __name__ == "__main__":
    asyncio.run(serve())