# Архитектура проекта

Проект `gRPC Document Microservice` построен на принципах **чистой архитектуры** и **Domain-Driven Design (DDD)**. Это обеспечивает модульность, тестируемость и легкость замены компонентов.

## Слои архитектуры

```
+-----------------------------+
|       gRPC Interface        |  # Входной адаптер (Protobuf)
+-----------------------------+
              |
              ▼
+-----------------------------+
|     Inbound Adapter Layer   |  # DocumentServiceServicer
+-----------------------------+
              |
              ▼
+-----------------------------+
|   Application / Services    |  # Бизнес-логика (DocumentService)
+-----------------------------+
              |
              ▼
+-----------------------------+
|       Domain Models         |  # DTOs, Entities, Ports
+-----------------------------+
              |
              ▼
+-----------------------------+
| Outbound Adapters / Repos   |  # MongoDB/PostgreSQL/Redis
+-----------------------------+
```

### 1. gRPC Interface
- Определен в `proto/service.proto`.
- Реализует CRUD, версионирование и восстановление документов.
- Использует асинхронный сервер (`grpc.aio`).

### 2. Inbound Adapter Layer
- Файл: `src/infra/adapters/inbound/grpc/adapter.py`.
- Преобразует gRPC-запросы в DTO и вызывает бизнес-логику.
- Обрабатывает ошибки и преобразует их в gRPC-статусы.

### 3. Application Layer
- Файл: `src/application/document/service.py`.
- Содержит бизнес-логику через `DocumentService`.
- Использует DI для доступа к репозиториям и кэшу.

### 4. Domain Layer
- Файлы: `src/domain/models/*`, `src/domain/dtos/*`, `src/domain/ports/*`.
- Определяет сущности (`Document`, `DocumentVersion`), DTO и интерфейсы (порты).
- Обеспечивает независимость от хранилищ и технологий.

### 5. Outbound Adapters
- **MongoDB**: `src/infra/adapters/outbound/mongo/*` с использованием `Beanie`.
- **PostgreSQL**: `src/infra/adapters/outbound/sql/*` с использованием `SQLAlchemy`.
- **Redis**: `src/infra/adapters/outbound/redis/*` для кэширования.

## Dependency Injection

- Используется `Dishka` для управления зависимостями.
- Файл: `src/infra/di/provider.py`.
- Обеспечивает гибкость при замене репозиториев (MongoDB/PostgreSQL).

## Базы данных

- **MongoDB**: Хранит документы в коллекции `documents` через `Beanie`.
- **PostgreSQL**: Использует таблицы `documents` и `document_versions` с JSONB для версий.
- Переключение между базами через `DB_TYPE` в `.env`.

## Кэширование

- **Redis**: Хранит документы, списки и версии.
- Ключи: `document:{id}`, `documents:skip={skip}:limit={limit}`, `document_versions:{id}`.
- TTL: 300 секунд (настраивается через `CACHE_TTL`).

## Преимущества архитектуры

- **Модульность**: Легкая замена хранилищ или добавление новых.
- **Тестируемость**: Четкие интерфейсы упрощают написание тестов.
- **Масштабируемость**: Поддержка асинхронности и кэширования.

---

[Вернуться к оглавлению](index.md)
```