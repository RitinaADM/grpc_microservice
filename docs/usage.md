# Использование API

Этот раздел описывает, как взаимодействовать с API микросервиса `gRPC Document Microservice` через gRPC.

## Подключение к gRPC-серверу

Сервер работает на порту `50051` (настраивается через `GRPC_PORT` в `.env`). Для взаимодействия используйте gRPC-клиент, например, `grpcurl` или клиент на Python.

### Пример проверки сервиса с `grpcurl`

```bash
grpcurl -plaintext localhost:50051 describe document.DocumentService
```

### Пример клиента на Python

```python
import grpc
from src.infra.adapters.inbound.grpc.py_proto import service_pb2, service_pb2_grpc

def main():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.DocumentServiceStub(channel)
        response = stub.GetDocument(service_pb2.GetDocumentRequest(id='123e4567-e89b-12d3-a456-426614174000'))
        print(response.document)

if __name__ == '__main__':
    main()
```

## Доступные методы

API предоставляет следующие методы (см. полную спецификацию в [api.md](api.md)):

1. **GetDocument**: Получение документа по ID.
2. **CreateDocument**: Создание нового документа.
3. **UpdateDocument**: Обновление документа.
4. **DeleteDocument**: Мягкое удаление документа.
5. **RestoreDocument**: Восстановление удаленного документа.
6. **ListDocuments**: Получение списка документов с пагинацией.
7. **GetDocumentVersions**: Получение списка версий документа.
8. **GetDocumentVersion**: Получение конкретной версии документа.

### Пример: Создание документа

```bash
grpcurl -plaintext -d '{
  "title": "My Document",
  "content": "This is a sample document.",
  "status": "DRAFT",
  "author": "John Doe",
  "tags": ["test", "sample"],
  "category": "General",
  "comments": ["Initial comment"]
}' localhost:50051 document.DocumentService/CreateDocument
```

### Пример: Получение документа

```bash
grpcurl -plaintext -d '{"id": "123e4567-e89b-12d3-a456-426614174000"}' \
  localhost:50051 document.DocumentService/GetDocument
```

## Кэширование

- Документы, списки и версии кэшируются в Redis с TTL 300 секунд (настраивается через `CACHE_TTL`).
- Изменения (создание, обновление, удаление) инвалидируют соответствующий кэш.

## Обработка ошибок

- **INVALID_ARGUMENT**: Ошибка валидации входных данных.
- **NOT_FOUND**: Документ или версия не найдены.
- **INTERNAL**: Внутренняя ошибка сервера.

---

[Вернуться к оглавлению](index.md)
```