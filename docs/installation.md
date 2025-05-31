
# Установка и запуск

Этот раздел описывает процесс установки и запуска микросервиса `gRPC Document Microservice`.

## Требования

- **Python**: 3.12
- **Docker** и **docker-compose**: Для контейнеризации
- **Git**: Для клонирования репозитория
- Базы данных: MongoDB 6.0, PostgreSQL 15, Redis 7.2 (запуск через docker-compose)

## Установка

1. **Клонирование репозитория**

   ```bash
   git clone https://github.com/RitinaADM/grpc_microservice.git
   cd grpc_microservice
   ```

2. **Настройка окружения**

   Проект использует файл `.env` для конфигурации. Выберите шаблон в зависимости от базы данных:

   - Для **PostgreSQL**: Скопируйте `.env.sql.example`.
   - Для **MongoDB**: Скопируйте `.env.nosql.example`.

   ```bash
   cp .env.sql.example .env
   ```

   Отредактируйте `.env` при необходимости:

   ```text
   DB_TYPE=POSTGRES
   DB_NAME=microservice_db
   MONGO_URL=
   POSTGRES_URL=postgresql+asyncpg://user:password@postgres:5432/microservice_db
   REDIS_URL=redis://redis:6379/0
   GRPC_PORT=50051
   LOG_LEVEL=INFO
   CACHE_TTL=300
   ```

3. **Установка зависимостей**

   Если вы запускаете без Docker, убедитесь, что зависимости установлены:

   ```bash
   pip install -r requirements.txt
   ```

## Запуск

### С использованием Docker

1. Запустите сервисы с помощью `docker-compose`:

   ```bash
   docker-compose up --build
   ```

   Это поднимет:
   - gRPC-сервер на порту `50051`.
   - MongoDB на порту `27017`.
   - PostgreSQL на порту `5432`.
   - Redis на порту `6379`.

2. Проверьте, что сервер доступен:

   ```bash
   grpcurl -plaintext localhost:50051 describe document.DocumentService
   ```

### Без Docker

1. Убедитесь, что MongoDB/PostgreSQL и Redis запущены локально.
2. Запустите приложение:

   ```bash
   python src/main.py
   ```

## Проверка работоспособности

- Сервер gRPC доступен на `localhost:50051`.
- Используйте `grpcurl` или клиентский код для проверки API (см. [Использование API](usage.md)).

## Остановка

Для остановки контейнеров выполните:

```bash
docker-compose down
```

---

[Вернуться к оглавлению](index.md)
```