
# Руководство для разработчиков

Этот раздел предназначен для разработчиков, желающих внести изменения в проект `gRPC Document Microservice` или расширить его функциональность.

## Структура проекта

```
grpc_microservice/
├── src/
│   ├── application/      # Сервисный слой (бизнес-логика)
│   ├── domain/           # Доменные модели, DTO, порты
│   ├── infra/            # Адаптеры для gRPC, баз данных, кэша
│   └── app.py, main.py   # Точки входа
├── proto/                # Protobuf спецификации
├── docs/                 # Документация
├── Dockerfile            # Конфигурация Docker
├── docker-compose.yml    # Оркестрация сервисов
├── .env, .env.*.example  # Настройки окружения
└── requirements.txt      # Зависимости
```

## Обновление Protobuf

Для обновления файлов `service_pb2.py` и `service_pb2_grpc.py`:

1. Выполните команду:

   ```bash
   python -m grpc_tools.protoc -Iproto \
       --python_out=src/infra/adapters/inbound/grpc/py_proto \
       --grpc_python_out=src/infra/adapters/inbound/grpc/py_proto \
       proto/service.proto
   ```

2. Исправьте импорт в `service_pb2_grpc.py`:

   Замените:

    ``` python
   import service_pb2 as service__pb2
    ```

   На:

   ``` python
   from src.infra.adapters.inbound.grpc.py_proto import service_pb2 as service__pb2
   ```

## Добавление нового метода

1. Обновите `proto/service.proto`, добавив новый метод и сообщения.
2. Сгенерируйте новые файлы Protobuf (см. выше).
3. Реализуйте логику в `src/infra/adapters/inbound/grpc/adapter.py` и `src/application/document/service.py`.
4. Обновите репозитории (`MongoDocumentAdapter` или `SQLDocumentAdapter`) при необходимости.

## Тестирование

Тесты пока отсутствуют. Рекомендуется добавить:

- **Юнит-тесты** для сервисов и адаптеров (`pytest`, `pytest-asyncio`).
- **Интеграционные тесты** для проверки взаимодействия с базами данных и gRPC.

Пример теста для `DocumentService`:

``` python
import pytest
from src.application.document.service import DocumentService
from src.domain.dtos.document import DocumentCreateDTO

@pytest.mark.asyncio
async def test_create_document():
    # Подготовка мока репозитория и кэша
    repository = MockRepository()
    cache = MockCache()
    service = DocumentService(repository, cache)
    
    dto = DocumentCreateDTO(title="Test", content="Content", status="DRAFT", author="Author")
    document = await service.create(dto)
    
    assert document.title == "Test"
```

## Логирование

- Логи настраиваются через `LOG_LEVEL` в `.env` (по умолчанию `INFO`).
- Логи пишутся в stdout в формате: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.

## Рекомендации

- **Индексы**: Добавьте индексы для MongoDB (`id`, `is_deleted`) и PostgreSQL (`documents.id`, `documents.is_deleted`).
- **CI/CD**: Настройте пайплайн для автоматической сборки и тестирования.
- **Мониторинг**: Интегрируйте Prometheus/Graphana для метрик.

---

[Вернуться к оглавлению](index.md)
```