import grpc
from typing import Callable, Any
from src.infra.auth.jwt_utils import JWTUtils, JWTAuthException
from src.infra.config.settings import settings
import logging

class JWTAuthInterceptor(grpc.aio.ServerInterceptor):
    """gRPC перехватчик для проверки JWT-токенов в метаданных."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.jwt_utils = JWTUtils()
        self.public_methods = ['ListDocuments', 'GetDocument']  # Публичные методы

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """Перехватывает gRPC-запросы для проверки авторизации."""
        method_name = handler_call_details.method.split('/')[-1]
        full_method = handler_call_details.method
        self.logger.debug(f"Обрабатывается метод: {method_name}, Полный путь: {full_method}")

        # Пропустить проверку авторизации для методов рефлексии gRPC
        if full_method.startswith('/grpc.reflection.'):
            self.logger.debug(f"Пропуск проверки авторизации для метода рефлексии: {full_method}")
            return await continuation(handler_call_details)

        # Пропустить проверку авторизации для публичных методов
        if method_name in self.public_methods:
            self.logger.debug(f"Пропуск проверки авторизации для публичного метода: {method_name}")
            return await continuation(handler_call_details)

        # Пропустить проверку авторизации, если JWT отключён
        if not settings.JWT_AUTH_ENABLED:
            self.logger.debug("JWT авторизация отключена, пропуск проверки")
            return await continuation(handler_call_details)

        # Получаем оригинальный обработчик
        handler = await continuation(handler_call_details)
        if not handler:
            return None

        # Оборачиваем обработчик, чтобы выполнять проверку авторизации
        async def auth_wrapper(request, context: grpc.aio.ServicerContext):
            try:
                metadata = dict(context.invocation_metadata())
                self.logger.debug(f"Получены метаданные: {metadata}")
                token = metadata.get("authorization")

                if not token:
                    self.logger.warning(f"JWT токен отсутствует для метода: {method_name}, peer: {context.peer()}")
                    await context.abort(
                        grpc.StatusCode.UNAUTHENTICATED,
                        "Токен авторизации отсутствует"
                    )

                if token.startswith("Bearer "):
                    token = token[7:]
                payload = self.jwt_utils.decode_token(token)
                self.logger.debug(f"Токен успешно проверен, payload: {payload}")

                # Вызов метода unary_unary обработчика
                if hasattr(handler, 'unary_unary'):
                    return await handler.unary_unary(request, context)
                else:
                    self.logger.error(f"Обработчик для {method_name} не является unary_unary")
                    await context.abort(grpc.StatusCode.INTERNAL, "Неверный тип обработчика")

            except JWTAuthException as e:
                self.logger.error(f"Ошибка авторизации для метода {method_name}: {str(e)}")
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
            except grpc._cython.cygrpc.AbortError:
                raise  # Повторно выбрасываем, чтобы завершить abort
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка при проверке токена для метода {method_name}: {str(e)}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, "Внутренняя ошибка сервера")

        # Возвращаем новый обработчик с обёрткой авторизации
        return grpc.unary_unary_rpc_method_handler(
            auth_wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer
        )