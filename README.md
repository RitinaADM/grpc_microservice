# grpc_microservice

python -m grpc_tools.protoc -Iproto --python_out=src/infra/adapters/inbound/grpc/py_proto --grpc_python_out=src/infra/adapters/inbound/grpc/py_proto proto/service.proto
from src.infra.adapters.inbound.grpc.py_proto import service_pb2 as service__pb2


# Архитектура проекта

Микросервис `grpc_microservice` построен на принципах **чистой архитектуры** (Clean Architecture) с использованием паттерна **порты и адаптеры** (Ports and Adapters). Это обеспечивает модульность, тестируемость и независимость бизнес-логики от внешних систем.

Микросервис для управления документами с поддержкой MongoDB/PostgreSQL, кэширования в Redis и gRPC API. Построен на принципах **чистой архитектуры** и паттерна **порты и адаптеры**, что обеспечивает модульность, тестируемость и независимость бизнес-логики от внешних систем.

## Возможности
- **CRUD операции**: Создание, получение, обновление и мягкое удаление документов.
- **Управление версиями**: Хранение и получение истории изменений документов.
- **Пагинация**: Получение списка документов с параметрами `skip` и `limit`.
- **Кэширование**: Использование Redis для кэширования документов, списков и версий.
- **Гибкое хранилище**: Поддержка MongoDB (`beanie`) и PostgreSQL (`SQLAlchemy`).
- **Обработка ошибок**: Специфичные исключения и gRPC-статусы (`NOT_FOUND`, `INVALID_ARGUMENT`, `INTERNAL`).
- **Повтор попыток**: Использование `tenacity` для обработки сбоев MongoDB и Redis.
- **Внедрение зависимостей**: Использование `dishka` для DI.

## Технологический стек
- **Язык**: Python 3.12 (асинхронный, `asyncio`).
- **API**: gRPC (`service.proto`).
- **Базы данных**:
  - MongoDB (`beanie`, `motor`).
  - PostgreSQL (`SQLAlchemy`, `asyncpg`).
- **Кэширование**: Redis (`redis-py`).
- **Валидация**: `pydantic` для DTO и настроек.
- **DI**: `dishka`.
- **Логирование**: Стандартная библиотека `logging`.
- **Тестирование**: `pytest`, `pytest-asyncio`.
- **Контейнеризация**: Docker, Docker Compose.

## Архитектура проекта

Проект разделён на три слоя согласно чистой архитектуре:

1. **Доменный слой** (`src/domain`):
   - Модели: `Document`, `DocumentVersion`, `DocumentStatus`.
   - DTO: `DocumentCreateDTO`, `DocumentUpdateDTO`, `DocumentListDTO`, `DocumentIdDTO`.
   - Порты: `DocumentServicePort`, `DocumentRepositoryPort`.
   - Исключения: `DocumentNotFoundException`, `InvalidInputException`.

2. **Прикладной слой** (`src/application`):
   - `DocumentService`: Реализация бизнес-логики CRUD, версионирования и пагинации.
   - Координирует взаимодействие с репозиториями и кэшем.

3. **Инфраструктурный слой** (`src/infra`):
   - **Входные адаптеры** (`inbound`): gRPC-сервис (`DocumentServiceServicer`).
   - **Выходные адаптеры** (`outbound`):
     - `MongoDocumentAdapter`, `SQLDocumentAdapter` для работы с БД.
     - `RedisCacheAdapter` для кэширования.
   - **Мапперы**: `GrpcMapper`, `MongoMapper`, `SQLMapper`, `RedisMapper`, `MapperUtils`, `VersionMapper`.
   - **Конфигурация**: `settings.py` (`.env`), `logging.py`.
   - **DI**: `provider.py` для настройки зависимостей.

## Технологический стек
- **Язык программирования**: Python 3.12 с асинхронной моделью (`asyncio`).
- **gRPC**: API определено в `proto/service.proto`, поддерживает методы `GetDocument`, `CreateDocument`, `UpdateDocument`, `DeleteDocument`, `RestoreDocument`, `ListDocuments`.
- **Базы данных**:
  - MongoDB (через `beanie` и `motor` для асинхронного доступа).
  - PostgreSQL (через `SQLAlchemy` с `asyncpg`).
- **Кэширование**: Redis (через `redis-py`).
- **Внедрение зависимостей**: `dishka` для управления зависимостями.
- **Валидация данных**: `pydantic` для DTO и настроек.
- **Логирование**: Стандартная библиотека `logging` с конфигурацией через `.env`.
- **Контейнеризация**: Docker и Docker Compose.

## Схема взаимодействия

[Клиент] --> [gRPC Сервис] --> [DocumentService] --> [MongoDB/PostgreSQL] --> [Redis Cache]

1. Клиент отправляет gRPC-запрос (например, `CreateDocument`).
2. Запрос обрабатывается `DocumentServiceServicer`, который преобразует gRPC-сообщения в DTO.
3. `DocumentService` выполняет бизнес-логику, проверяет кэш в Redis и, при необходимости, обращается к базе данных через `DocumentRepositoryPort`.
4. Данные сохраняются/получаются из MongoDB или PostgreSQL в зависимости от настройки `DB_TYPE`.
5. Результат кэшируется в Redis и возвращается клиенту через gRPC.

## Ключевые особенности
- **Абстракция хранилища**: Единый интерфейс `DocumentRepositoryPort` позволяет переключаться между MongoDB и PostgreSQL без изменения бизнес-логики.
- **Кэширование**: Redis используется для кэширования документов и списков документов, с инвалидацией кэша при обновлениях.
- **Обработка ошибок**: Специфичные исключения (`DocumentNotFoundException`, `BaseAppException`) и соответствующие gRPC-статусы (`NOT_FOUND`, `INVALID_ARGUMENT`, `INTERNAL`).
- **Повтор попыток**: Используется `tenacity` для повторных попыток при сбоях MongoDB.

