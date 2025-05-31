import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from src.infra.config.settings import settings
from src.domain.exceptions.base import BaseAppException


class JWTAuthException(BaseAppException):
    """Исключение для ошибок авторизации."""

    def __str__(self):
        return "Ошибка авторизации"


class JWTUtils:
    """Утилиты для работы с JWT-токенами."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.token_ttl = settings.JWT_TOKEN_TTL

    def create_token(self, payload: Dict) -> str:
        """Создает JWT-токен с указанным payload."""
        try:
            payload["exp"] = datetime.utcnow() + timedelta(seconds=self.token_ttl)
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            self.logger.debug("JWT-токен успешно создан")
            return token
        except Exception as e:
            self.logger.error(f"Ошибка при создании JWT-токена: {str(e)}")
            raise JWTAuthException(f"Не удалось создать токен: {str(e)}")

    def decode_token(self, token: str) -> Dict:
        """Декодирует и проверяет JWT-токен."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.logger.debug("JWT-токен успешно декодирован")
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT-токен истек")
            raise JWTAuthException("Токен истек")
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Неверный JWT-токен: {str(e)}")
            raise JWTAuthException("Неверный токен")
        except Exception as e:
            self.logger.error(f"Ошибка при декодировании JWT-токена: {str(e)}")
            raise JWTAuthException(f"Ошибка декодирования токена: {str(e)}")