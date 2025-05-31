# Спецификация gRPC API

Этот раздел описывает API сервиса `DocumentService`, определенного в `proto/service.proto`.

## Определение сервиса

```protobuf
service DocumentService {
    rpc GetDocument (GetDocumentRequest) returns (GetDocumentResponse);
    rpc CreateDocument (CreateDocumentRequest) returns (Document);
    rpc UpdateDocument (UpdateDocumentRequest) returns (UpdateDocumentResponse);
    rpc DeleteDocument (DeleteDocumentRequest) returns (DeleteDocumentResponse);
    rpc RestoreDocument (RestoreDocumentRequest) returns (Document);
    rpc ListDocuments (ListDocumentsRequest) returns (ListDocumentsResponse);
    rpc GetDocumentVersions (GetDocumentVersionsRequest) returns (GetDocumentVersionsResponse);
    rpc GetDocumentVersion (GetDocumentVersionRequest) returns (DocumentVersion);
}
```

## Типы данных

### DocumentStatus

```protobuf
enum DocumentStatus {
    DRAFT = 0;
    PUBLISHED = 1;
    ARCHIVED = 2;
}
```

### Document

```protobuf
message Document {
    string id = 1;              // UUID документа
    string title = 2;           // Заголовок
    string content = 3;         // Содержимое
    DocumentStatus status = 4;  // Статус
    string author = 5;          // Автор
    repeated string tags = 6;   // Теги
    string category = 7;        // Категория
    repeated string comments = 8; // Комментарии
    string created_at = 9;      // Дата создания (ISO)
    string updated_at = 10;     // Дата обновления (ISO)
    bool is_deleted = 11;       // Флаг мягкого удаления
}
```

### DocumentVersion

```protobuf
message DocumentVersion {
    string version_id = 1;      // UUID версии
    Document document = 2;      // Данные документа
    string timestamp = 3;       // Время создания версии (ISO)
}
```

## Методы

### 1. GetDocument

**Описание**: Получает документ по ID.

**Запрос**:

```protobuf
message GetDocumentRequest {
    string id = 1;  // UUID документа
}
```

**Ответ**:

```protobuf
message GetDocumentResponse {
    Document document = 1;  // Данные документа
}
```

**Ошибки**:
- `NOT_FOUND`: Документ не найден.
- `INVALID_ARGUMENT`: Неверный формат UUID.

### 2. CreateDocument

**Описание**: Создает новый документ.

**Запрос**:

```protobuf
message CreateDocumentRequest {
    string title = 1;
    string content = 2;
    DocumentStatus status = 3;
    string author = 4;
    repeated string tags = 5;
    string category = 6;
    repeated string comments = 7;
}
```

**Ответ**:

```protobuf
message Document { ... }  // Созданный документ
```

**Ошибки**:
- `INVALID_ARGUMENT`: Пустые обязательные поля или неверный статус.

### 3. UpdateDocument

**Описание**: Обновляет существующий документ.

**Запрос**:

```protobuf
message UpdateDocumentRequest {
    string id = 1;
    string title = 2;
    string content = 3;
    DocumentStatus status = 4;
    string author = 5;
    repeated string tags = 6;
    string category = 7;
    repeated string comments = 8;
}
```

**Ответ**:

```protobuf
message UpdateDocumentResponse {
    Document document = 1;  // Обновленный документ
}
```

**Ошибки**:
- `NOT_FOUND`: Документ не найден.
- `INVALID_ARGUMENT`: Неверный формат UUID или данных.

### 4. DeleteDocument

**Описание**: Выполняет мягкое удаление документа.

**Запрос**:

```protobuf
message DeleteDocumentRequest {
    string id = 1;  // UUID документа
}
```

**Ответ**:

```protobuf
message DeleteDocumentResponse {
    bool success = 1;  // Успех операции
}
```

**Ошибки**:
- `NOT_FOUND`: Документ не найден.

### 5. RestoreDocument

**Описание**: Восстанавливает удаленный документ.

**Запрос**:

```protobuf
message RestoreDocumentRequest {
    string id = 1;  // UUID документа
}
```

**Ответ**:

```protobuf
message Document { ... }  // Восстановленный документ
```

**Ошибки**:
- `NOT_FOUND`: Документ не найден или не был удален.

### 6. ListDocuments

**Описание**: Получает список документов с пагинацией.

**Запрос**:

```protobuf
message ListDocumentsRequest {
    int32 skip = 1;  // Количество пропущенных записей
    int32 limit = 2; // Лимит записей
}
```

**Ответ**:

```protobuf
message ListDocumentsResponse {
    repeated Document documents = 1;  // Список документов
}
```

**Ошибки**:
- `INVALID_ARGUMENT`: Отрицательный `skip`.

### 7. GetDocumentVersions

**Описание**: Получает список версий документа.

**Запрос**:

```protobuf
message GetDocumentVersionsRequest {
    string id = 1;  // UUID документа
}
```

**Ответ**:

```protobuf
message GetDocumentVersionsResponse {
    repeated DocumentVersion versions = 1;  // Список версий
}
```

**Ошибки**:
- `NOT_FOUND`: Документ не найден.

### 8. GetDocumentVersion

**Описание**: Получает конкретную версию документа.

**Запрос**:

```protobuf
message GetDocumentVersionRequest {
    string id = 1;         // UUID документа
    string version_id = 2; // UUID версии
}
```

**Ответ**:

```protobuf
message DocumentVersion { ... }  // Данные версии
```

**Ошибки**:
- `NOT_FOUND`: Документ или версия не найдены.

---


[Вернуться к оглавлению](index.md)
```