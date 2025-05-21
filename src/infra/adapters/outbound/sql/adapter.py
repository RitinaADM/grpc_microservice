from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.domain.models.document import Document
from src.infra.adapters.outbound.sql.models import SQLDocument
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.dtos.document import DocumentUpdateDTO
import logging
from logging import Logger


class SQLDocumentAdapter(DocumentRepositoryPort):
    """Адаптер для работы с PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Инициализация адаптера с сессией SQLAlchemy."""
        self.session: AsyncSession = session
        self.logger: Logger = logging.getLogger(__name__)

    async def _ensure_no_active_transaction(self):
        """Проверяет, что на сессии нет активной транзакции."""
        if self.session.in_transaction():
            self.logger.warning("Session has an active transaction; rolling back")
            await self.session.rollback()

    async def get_by_id(self, id: UUID) -> Optional[Document]:
        """Получение документа по ID из PostgreSQL (без транзакции)."""
        self.logger.debug(f"Fetching document from PostgreSQL with ID: {id}")
        result = await self.session.execute(
            select(SQLDocument).where(SQLDocument.id == id, SQLDocument.is_deleted == False)
        )
        sql_doc = result.scalars().first()
        return self._to_domain(sql_doc) if sql_doc else None

    async def create(self, document: Document) -> Document:
        """Создание документа в PostgreSQL с транзакцией."""
        self.logger.debug(f"Creating document in PostgreSQL: {document.id}")
        await self._ensure_no_active_transaction()
        async with self.session.begin():  # Открываем транзакцию
            sql_doc = self._to_sql(document)
            self.session.add(sql_doc)
            await self.session.flush()  # Синхронизируем данные без коммита
            await self.session.refresh(sql_doc)  # Обновляем объект
        return self._to_domain(sql_doc)

    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        """Обновление документа в PostgreSQL с транзакцией."""
        self.logger.debug(f"Updating document in PostgreSQL with ID: {id}, data: {data.dict(exclude_none=True)}")
        await self._ensure_no_active_transaction()
        async with self.session.begin():  # Открываем транзакцию
            update_data = {k: v for k, v in data.dict(exclude_none=True).items() if k != 'id'}
            if not update_data:
                return await self.get_by_id(id)  # Если нет данных для обновления, возвращаем текущий документ
            update_data['updated_at'] = datetime.utcnow()
            result = await self.session.execute(
                update(SQLDocument)
                .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                .values(**update_data)
                .returning(SQLDocument)  # Возвращаем обновленный объект
            )
            sql_doc = result.scalars().first()
            if not sql_doc:
                return None
            return self._to_domain(sql_doc)

    async def delete(self, id: UUID) -> bool:
        """Мягкое удаление документа из PostgreSQL с транзакцией."""
        self.logger.debug(f"Starting soft delete for document ID: {id}")
        await self._ensure_no_active_transaction()
        async with self.session.begin():  # Открываем транзакцию
            result = await self.session.execute(
                update(SQLDocument)
                .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                .values(is_deleted=True, updated_at=datetime.utcnow())
            )
            self.logger.debug(f"Soft delete result: {result.rowcount} rows affected")
        self.logger.debug(f"Completed soft delete for document ID: {id}")
        return result.rowcount > 0

    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        """Получение списка документов из PostgreSQL с пагинацией (без транзакции)."""
        self.logger.debug(f"Fetching documents from PostgreSQL with skip: {skip}, limit: {limit}")
        result = await self.session.execute(
            select(SQLDocument)
            .where(SQLDocument.is_deleted == False)
            .order_by(SQLDocument.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        sql_docs = result.scalars().all()
        return [self._to_domain(doc) for doc in sql_docs]

    async def restore(self, id: UUID) -> Optional[Document]:
        """Восстановление документа в PostgreSQL с транзакцией."""
        self.logger.debug(f"Starting restore for document ID: {id}")
        await self._ensure_no_active_transaction()
        async with self.session.begin():  # Открываем транзакцию
            result = await self.session.execute(
                update(SQLDocument)
                .where(SQLDocument.id == id, SQLDocument.is_deleted == True)
                .values(is_deleted=False, updated_at=datetime.utcnow())
                .returning(SQLDocument)  # Возвращаем обновленный объект
            )
            sql_doc = result.scalars().first()
            self.logger.debug(f"Restore result: {'success' if sql_doc else 'not found'} for document ID: {id}")
            if not sql_doc:
                return None
            return self._to_domain(sql_doc)

    def _to_domain(self, sql_doc: Optional[SQLDocument]) -> Optional[Document]:
        """Конвертация SQLAlchemy модели в доменную модель."""
        if not sql_doc:
            return None
        return Document(
            id=sql_doc.id,
            title=sql_doc.title,
            content=sql_doc.content,
            created_at=sql_doc.created_at,
            updated_at=sql_doc.updated_at,
            is_deleted=sql_doc.is_deleted
        )

    def _to_sql(self, document: Document) -> SQLDocument:
        """Конвертация доменной модели в SQLAlchemy модель."""
        return SQLDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            created_at=document.created_at,
            updated_at=document.updated_at,
            is_deleted=document.is_deleted
        )