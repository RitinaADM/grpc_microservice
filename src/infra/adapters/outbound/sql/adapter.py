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

class SQLDocumentAdapter(DocumentRepositoryPort):
    """Адаптер для работы с PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Инициализация адаптера с сессией SQLAlchemy."""
        self.session: AsyncSession = session

    async def get_by_id(self, id: UUID) -> Optional[Document]:
        """Получение документа по ID из PostgreSQL."""
        result = await self.session.execute(
            select(SQLDocument).where(SQLDocument.id == id, SQLDocument.is_deleted == False)
        )
        sql_doc = result.scalars().first()
        return self._to_domain(sql_doc) if sql_doc else None

    async def create(self, document: Document) -> Document:
        """Создание документа в PostgreSQL."""
        sql_doc = self._to_sql(document)
        self.session.add(sql_doc)
        await self.session.commit()
        await self.session.refresh(sql_doc)
        return self._to_domain(sql_doc)

    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        """Обновление документа в PostgreSQL."""
        update_data = {k: v for k, v in data.dict(exclude_none=True).items() if k != 'id'}
        if not update_data:
            return await self.get_by_id(id)  # Если нет данных для обновления, возвращаем текущий документ
        update_data['updated_at'] = datetime.utcnow()
        await self.session.execute(
            update(SQLDocument)
            .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
            .values(**update_data)
        )
        await self.session.commit()
        return await self.get_by_id(id)

    async def delete(self, id: UUID) -> bool:
        """Мягкое удаление документа из PostgreSQL."""
        result = await self.session.execute(
            update(SQLDocument)
            .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
            .values(is_deleted=True, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0

    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        """Получение списка документов из PostgreSQL с пагинацией."""
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
        """Восстановление документа в PostgreSQL."""
        result = await self.session.execute(
            update(SQLDocument)
            .where(SQLDocument.id == id, SQLDocument.is_deleted == True)
            .values(is_deleted=False, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        if result.rowcount > 0:
            return await self.get_by_id(id)
        return None

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