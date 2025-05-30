from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from src.domain.models.document import Document, DocumentVersion
from src.infra.adapters.outbound.sql.models import SQLDocument, SQLDocumentVersion
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.dtos.document import DocumentUpdateDTO
import logging
from logging import Logger
from src.infra.adapters.outbound.sql.mapper import SQLMapper

class SQLDocumentAdapter(DocumentRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session
        self.logger: Logger = logging.getLogger(__name__)
        self.mapper = SQLMapper()

    async def get_by_id(self, id: UUID) -> Optional[Document]:
        """
        Получает документ из PostgreSQL по его UUID.

        Args:
            id: UUID документа.

        Returns:
            Document: Доменная модель документа, если найден.
            None: Если документ не найден или помечен как удаленный.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Получение документа с id={id}")
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    select(SQLDocument)
                    .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                )
                sql_doc = result.scalars().first()
                if sql_doc:
                    self.logger.debug(f"Документ с id={id} найден")
                    return self.mapper.to_domain_document(sql_doc)
                self.logger.warning(f"Документ с id={id} не найден или удален")
                return None
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при получении документа: {str(e)}")
            raise

    async def create(self, document: Document) -> Document:
        """
        Создает новый документ в PostgreSQL.

        Args:
            document: Доменная модель документа.

        Returns:
            Document: Созданная доменная модель документа.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Создание документа в PostgreSQL: {document.id}")
        async with self.session.begin():
            try:
                sql_doc = self.mapper.to_sql_document(document)
                self.session.add(sql_doc)
                await self.session.flush()
                for version in document.versions:
                    sql_version = self.mapper.to_sql_version(version, document.id)
                    self.session.add(sql_version)
                await self.session.flush()
                result = await self.session.execute(
                    select(SQLDocument)
                    .where(SQLDocument.id == document.id)
                )
                sql_doc = result.scalars().first()
                self.logger.debug(f"Документ с ID {document.id} успешно создан")
                return self.mapper.to_domain_document(sql_doc)
            except SQLAlchemyError as e:
                self.logger.error(f"Ошибка при создании документа с ID {document.id}: {str(e)}")
                raise

    async def update(self, id: UUID, data: DocumentUpdateDTO) -> Optional[Document]:
        """
        Обновляет документ в PostgreSQL по его UUID.

        Args:
            id: UUID документа.
            data: DTO с данными для обновления.

        Returns:
            Document: Обновленная доменная модель документа, если найден.
            None: Если документ не найден или помечен как удаленный.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Обновление документа в PostgreSQL с ID: {id}")
        async with self.session.begin():
            try:
                result = await self.session.execute(
                    select(SQLDocument)
                    .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                )
                sql_doc = result.scalars().first()
                if not sql_doc:
                    self.logger.warning(f"Документ с ID: {id} не найден или помечен как удаленный")
                    return None

                sql_version = SQLDocumentVersion(
                    version_id=uuid4(),
                    document_id=id,
                    content=sql_doc.content,
                    document_metadata=sql_doc.document_metadata,
                    comments=sql_doc.comments,
                    timestamp=datetime.utcnow()
                )
                self.session.add(sql_version)
                await self.session.flush()
                self.logger.debug(f"Сохранена версия документа с ID: {id}, version_id: {sql_version.version_id}")

                update_data = {"updated_at": datetime.utcnow()}
                if data.title is not None:
                    update_data['title'] = data.title
                if data.content is not None:
                    update_data['content'] = data.content
                if data.status is not None:
                    update_data['status'] = data.status
                if data.metadata is not None:
                    update_data['document_metadata'] = data.metadata.dict()
                if data.comments is not None:
                    update_data['comments'] = data.comments

                result = await self.session.execute(
                    update(SQLDocument)
                    .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                    .values(**update_data)
                    .returning(SQLDocument)
                )
                sql_doc = result.scalars().first()
                self.logger.debug(f"Документ с ID: {id} успешно обновлен")
                return self.mapper.to_domain_document(sql_doc)
            except SQLAlchemyError as e:
                self.logger.error(f"Ошибка при обновлении документа с ID {id}: {str(e)}")
                await self.session.rollback()
                raise

    async def delete(self, id: UUID) -> bool:
        """
        Выполняет мягкое удаление документа в PostgreSQL.

        Args:
            id: UUID документа.

        Returns:
            bool: True, если документ успешно помечен как удаленный, иначе False.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Начало мягкого удаления для документа с ID: {id}")
        async with self.session.begin():
            try:
                result = await self.session.execute(
                    select(SQLDocument)
                    .where(SQLDocument.id == id, SQLDocument.is_deleted == False)
                )
                sql_doc = result.scalars().first()
                if not sql_doc:
                    self.logger.info(f"Документ с ID: {id} уже удален или не существует")
                    return False
                result = await self.session.execute(
                    update(SQLDocument)
                    .where(SQLDocument.id == id)
                    .values(is_deleted=True, updated_at=datetime.utcnow())
                )
                self.logger.debug(f"Документ с ID: {id} успешно помечен как удаленный")
                return True
            except SQLAlchemyError as e:
                self.logger.error(f"Ошибка при удалении документа с ID {id}: {str(e)}")
                await self.session.rollback()
                raise

    async def list_documents(self, skip: int, limit: int) -> List[Document]:
        """
        Получает список документов из PostgreSQL с пагинацией.

        Args:
            skip: Количество документов для пропуска.
            limit: Максимальное количество документов для возврата.

        Returns:
            List[Document]: Список доменных моделей документов.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Получение списка документов из PostgreSQL с skip={skip}, limit={limit}")
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    select(SQLDocument)
                    .options(joinedload(SQLDocument.versions))
                    .where(SQLDocument.is_deleted == False)
                    .order_by(SQLDocument.updated_at.desc())
                    .offset(skip)
                    .limit(limit)
                )
                sql_docs = result.unique().scalars().all()
                self.logger.debug(f"Получено {len(sql_docs)} документов: {[doc.id for doc in sql_docs]}")
                return [self.mapper.to_domain_document(doc) for doc in sql_docs]
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при получении списка документов: {str(e)}")
            raise

    async def restore(self, id: UUID) -> Optional[Document]:
        """
        Восстанавливает удаленный документ в PostgreSQL.

        Args:
            id: UUID документа.

        Returns:
            Document: Восстановленная доменная модель документа, если найдена.
            None: Если документ не найден.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Начало восстановления для документа с ID: {id}")
        async with self.session.begin():
            try:
                result = await self.session.execute(
                    update(SQLDocument)
                    .where(SQLDocument.id == id, SQLDocument.is_deleted == True)
                    .values(is_deleted=False, updated_at=datetime.utcnow())
                    .returning(SQLDocument)
                )
                sql_doc = result.scalars().first()
                if sql_doc:
                    result = await self.session.execute(
                        select(SQLDocument)
                        .where(SQLDocument.id == id)
                    )
                    sql_doc = result.scalars().first()
                self.logger.debug(f"Результат восстановления: {'успех' if sql_doc else 'не найдено'} для документа с ID: {id}")
                return self.mapper.to_domain_document(sql_doc) if sql_doc else None
            except SQLAlchemyError as e:
                self.logger.error(f"Ошибка при восстановлении документа с ID {id}: {str(e)}")
                await self.session.rollback()
                raise

    async def get_versions(self, id: UUID) -> List[DocumentVersion]:
        """
        Получает список версий документа из PostgreSQL.

        Args:
            id: UUID документа.

        Returns:
            List[DocumentVersion]: Список доменных моделей версий документа.

        Raises:
            SQLAlchemyError: Если произошла ошибка базы данных.
        """
        self.logger.debug(f"Получение версий для документа с id={id}")
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    select(SQLDocumentVersion)
                    .where(SQLDocumentVersion.document_id == id)
                    .order_by(SQLDocumentVersion.timestamp.desc())
                )
                sql_versions = result.scalars().all()
                self.logger.debug(f"Получено {len(sql_versions)} версий для документа с id={id}")
                return [self.mapper.to_domain_version(v) for v in sql_versions]
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при получении версий документа с id={id}: {str(e)}")
            raise