# gRPC Document Microservice

> *"Учиться на лучшем — значит творить лучшее."*

**gRPC Document Microservice** — это современный микросервис для управления документами, построенный на основе **gRPC**, **чистой архитектуры** и **Domain-Driven Design (DDD)**. Он предоставляет функциональность для создания, обновления, удаления, восстановления и версионирования документов с поддержкой MongoDB или PostgreSQL и кэшированием через Redis.

## Основные возможности

- 📝 **Полный CRUD**: Создание, чтение, обновление и мягкое удаление документов.
- 🔄 **Версионирование**: Хранение и восстановление предыдущих версий документов.
- 🗄 **Гибкость хранилищ**: Поддержка MongoDB и PostgreSQL с переключением через конфигурацию.
- ⚡ **Кэширование**: Использование Redis для повышения производительности.
- 🛠 **Чистая архитектура**: Модульная структура с разделением слоев.
- 🔗 **Dependency Injection**: Управление зависимостями через `Dishka`.
- 🐳 **Контейнеризация**: Легкое развертывание с Docker и docker-compose.

## Технологии

| Категория       | Технологии                                  |
|-----------------|---------------------------------------------|
| Язык            | Python 3.12                                |
| gRPC            | `grpcio`, `grpcio-tools`, `protobuf`       |
| DI              | `Dishka`                                   |
| ORM/ODM         | `SQLAlchemy` (PostgreSQL), `Beanie` (MongoDB) |
| Кэш             | `Redis`, `redis-py`, `tenacity`            |
| Валидация       | `Pydantic v2`                              |
| Логирование     | `logging`                                  |
| Контейнеризация | `Docker`, `docker-compose`                 |

## Начало работы

1. **Клонируйте репозиторий**:

   ```bash
   git clone https://github.com/RitinaADM/grpc_microservice.git
   cd grpc_microservice
   ```

2. **Настройте окружение**:

   Скопируйте `.env.sql.example` или `.env.nosql.example` в `.env` и настройте параметры:

   ```bash
   cp .env.sql.example .env
   ```

3. **Запустите с Docker**:

   ```bash
   docker-compose up --build
   ```

   Сервер будет доступен на `localhost:50051`.

4. **Проверьте API**:

   ```bash
   grpcurl -plaintext localhost:50051 describe document.DocumentService
   ```

Подробные инструкции по установке и использованию см. в [документации](docs/installation.md).

## Структура проекта

```
grpc_microservice/
├── src/                  # Исходный код
│   ├── application/      # Бизнес-логика
│   ├── domain/           # Доменные модели и порты
│   ├── infra/            # Адаптеры (gRPC, базы данных, кэш)
│   └── app.py, main.py   # Точки входа
├── proto/                # Protobuf файлы
├── docs/                 # Документация
├── Dockerfile            # Конфигурация Docker
├── docker-compose.yml    # Оркестрация сервисов
├── .env, .env.*.example  # Настройки окружения
└── requirements.txt      # Зависимости
```

## Документация

Полная документация доступна в директории `/docs`:

- [Установка и запуск](docs/installation.md)
- [Использование API](docs/usage.md)
- [Архитектура проекта](docs/architecture.md)
- [Спецификация API](docs/api.md)
- [Руководство для разработчиков](docs/development.md)
- [Решение проблем](docs/troubleshooting.md)

## Лицензия

Проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## Контрибьюция

Приветствуются любые улучшения! Пожалуйста, создавайте issues или pull requests в репозитории. Ознакомьтесь с [руководством для разработчиков](docs/development.md) перед началом работы.

---

*Создано с ❤️ для сообщества разработчиков.*
```