# grpc_microservice

python -m grpc_tools.protoc -Iproto --python_out=src/infra/adapters/inbound/grpc/py_proto --grpc_python_out=src/infra/adapters/inbound/grpc/py_proto proto/service.proto
from src.infra.adapters.inbound.grpc.py_proto import service_pb2 as service__pb2


# Архитектура проекта

Микросервис `grpc_microservice` построен на принципах **чистой архитектуры** (Clean Architecture) с использованием паттерна **порты и адаптеры** (Ports and Adapters). Это обеспечивает модульность, тестируемость и независимость бизнес-логики от внешних систем.

## Слои архитектуры

Проект разделён на три основных слоя:

1. **Доменный слой** (`src/domain`):
   - Содержит бизнес-логику и модели данных:
     - `Document`: Модель документа с полями `id`, `title`, `content`, `created_at`, `updated_at`, `is_deleted`.
     - DTO (Data Transfer Objects): `DocumentCreateDTO`, `DocumentUpdateDTO`, `DocumentListDTO`, `DocumentIdDTO` для валидации входных данных.
   - Определяет интерфейсы (порты):
     - `DocumentServicePort`: Интерфейс для бизнес-логики.
     - `DocumentRepositoryPort`: Интерфейс для взаимодействия с хранилищем данных.
   - Независим от внешних технологий и не содержит кода, связанного с базами данных или gRPC.

2. **Прикладной слой** (`src/application`):
   - Реализует бизнес-логику через класс `DocumentService`.
   - Координирует взаимодействие между доменным слоем и инфраструктурой.
   - Обрабатывает операции CRUD, восстановление документов и пагинацию, используя кэширование через Redis.

3. **Инфраструктурный слой** (`src/infra`):
   - **Входные адаптеры** (`src/infra/adapters/inbound`):
     - gRPC-сервис (`DocumentServiceServicer`), обрабатывающий запросы клиентов.
   - **Выходные адаптеры** (`src/infra/adapters/outbound`):
     - `MongoDocumentAdapter`: Реализация для MongoDB с использованием `beanie`.
     - `SQLDocumentAdapter`: Реализация для PostgreSQL с использованием `SQLAlchemy`.
     - `RedisCacheAdapter`: Кэширование данных в Redis.
   - **Конфигурация** (`src/infra/config`):
     - `settings.py`: Загрузка конфигурации из `.env`.
     - `logging.py`: Настройка логирования.
   - **DI** (`src/infra/di`):
     - Используется библиотека `dishka` для внедрения зависимостей.

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

