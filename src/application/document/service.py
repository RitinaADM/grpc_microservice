from uuid import UUID
from src.domain.models.document import Document
from src.domain.ports.inbound.services.document import DocumentServicePort
from src.domain.ports.outbound.repository.document import DocumentRepositoryPort
from src.domain.exceptions.document import DocumentNotFoundException
from src.domain.dtos.document import DocumentCreateDTO, DocumentUpdateDTO, DocumentListDTO, DocumentIdDTO
from typing import List
import logging
from pymongo.errors import ConnectionFailure, OperationFailure
from src.domain.exceptions.base import BaseAppException

class DocumentService(DocumentServicePort):
    def __init__(self, repository: DocumentRepositoryPort):
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def get_by_id(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Fetching document with ID: {id_dto.id}")
        try:
            document = await self.repository.get_by_id(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            self.logger.debug(f"Successfully fetched document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def create(self, data: DocumentCreateDTO) -> Document:
        self.logger.info(f"Creating document with title: {data.title}")
        try:
            document = Document(**data.dict())
            created_document = await self.repository.create(document)
            self.logger.debug(f"Successfully created document: {created_document.id}")
            return created_document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def update(self, id_dto: DocumentIdDTO, data: DocumentUpdateDTO) -> Document:
        self.logger.info(f"Updating document with ID: {id_dto.id}, data: {data.dict(exclude_none=True)}")
        try:
            document = await self.repository.update(id_dto.id, data.dict(exclude_none=True))
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            self.logger.debug(f"Successfully updated document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def delete(self, id_dto: DocumentIdDTO) -> bool:
        self.logger.info(f"Soft deleting document with ID: {id_dto.id}")
        try:
            success = await self.repository.delete(id_dto.id)
            if not success:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            self.logger.debug(f"Successfully soft deleted document: {id_dto.id}")
            return success
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def list_documents(self, params: DocumentListDTO) -> List[Document]:
        self.logger.info(f"Listing documents with skip: {params.skip}, limit: {params.limit}")
        try:
            documents = await self.repository.list_documents(params.skip, params.limit)
            self.logger.debug(f"Successfully fetched {len(documents)} documents")
            return documents
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")

    async def restore(self, id_dto: DocumentIdDTO) -> Document:
        self.logger.info(f"Restoring document with ID: {id_dto.id}")
        try:
            document = await self.repository.restore(id_dto.id)
            if not document:
                self.logger.warning(f"Document not found: {id_dto.id}")
                raise DocumentNotFoundException()
            self.logger.debug(f"Successfully restored document: {id_dto.id}")
            return document
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"Database error: {str(e)}")
            raise BaseAppException(f"Database error: {str(e)}")